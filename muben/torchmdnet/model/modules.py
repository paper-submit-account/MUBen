"""
# Modified: August 26th, 2023
# ---------------------------------------
# Description: Equivariant Transformer Network Components.
# Reference: https://github.com/shehzaidi/pre-training-via-denoising.
"""
import math
import torch
from torch import nn
import torch.nn.functional as F
from torch_geometric.nn import MessagePassing
from torch_cluster import radius_graph


class NeighborEmbedding(MessagePassing):
    """
    Create an embedding for the neighbors of each node in the graph.

    This class uses a Message Passing mechanism to create an embedding for
    each neighbor in the graph.

    Parameters
    ----------
    hidden_channels : int
        The number of channels in the hidden layer.
    num_rbf : int
        Number of radial basis functions.
    cutoff_lower : float
        Lower bound of the cutoff function.
    cutoff_upper : float
        Upper bound of the cutoff function.
    max_z : int, optional, default=100
        Maximum number of atomic numbers to consider in the embedding.
    """

    def __init__(
        self, hidden_channels, num_rbf, cutoff_lower, cutoff_upper, max_z=100
    ):
        super(NeighborEmbedding, self).__init__(aggr="add")
        self.embedding = nn.Embedding(max_z, hidden_channels)
        self.distance_proj = nn.Linear(num_rbf, hidden_channels)
        self.combine = nn.Linear(hidden_channels * 2, hidden_channels)
        self.cutoff = CosineCutoff(cutoff_lower, cutoff_upper)

        self.reset_parameters()

    def reset_parameters(self):
        self.embedding.reset_parameters()
        nn.init.xavier_uniform_(self.distance_proj.weight)
        nn.init.xavier_uniform_(self.combine.weight)
        self.distance_proj.bias.data.fill_(0)
        self.combine.bias.data.fill_(0)

    def forward(self, z, x, edge_index, edge_weight, edge_attr):
        # remove self loops
        mask = edge_index[0] != edge_index[1]
        if not mask.all():
            edge_index = edge_index[:, mask]
            edge_weight = edge_weight[mask]
            edge_attr = edge_attr[mask]

        C = self.cutoff(edge_weight)
        W = self.distance_proj(edge_attr) * C.view(-1, 1)

        x_neighbors = self.embedding(z)
        # propagate_type: (x: Tensor, W: Tensor)
        x_neighbors = self.propagate(edge_index, x=x_neighbors, W=W, size=None)
        x_neighbors = self.combine(torch.cat([x, x_neighbors], dim=1))
        return x_neighbors

    def message(self, x_j, W):
        return x_j * W


class GaussianSmearing(nn.Module):
    """
    Implements Gaussian smearing of distances.

    Smearing functions are used to create a smooth representation of distances.

    Parameters
    ----------
    cutoff_lower : float, optional, default=0.0
        Lower bound for the smearing function.
    cutoff_upper : float, optional, default=5.0
        Upper bound for the smearing function.
    num_rbf : int, optional, default=50
        Number of radial basis functions.
    trainable : bool, optional, default=True
        If True, the parameters of smearing can be optimized.
    """

    def __init__(
        self, cutoff_lower=0.0, cutoff_upper=5.0, num_rbf=50, trainable=True
    ):
        super(GaussianSmearing, self).__init__()
        self.cutoff_lower = cutoff_lower
        self.cutoff_upper = cutoff_upper
        self.num_rbf = num_rbf
        self.trainable = trainable

        offset, coeff = self._initial_params()
        if trainable:
            self.register_parameter("coeff", nn.Parameter(coeff))
            self.register_parameter("offset", nn.Parameter(offset))
        else:
            self.register_buffer("coeff", coeff)
            self.register_buffer("offset", offset)

    def _initial_params(self):
        offset = torch.linspace(
            self.cutoff_lower, self.cutoff_upper, self.num_rbf
        )
        coeff = -0.5 / (offset[1] - offset[0]) ** 2
        return offset, coeff

    def reset_parameters(self):
        offset, coeff = self._initial_params()
        self.offset.data.copy_(offset)
        self.coeff.data.copy_(coeff)

    def forward(self, dist):
        dist = dist.unsqueeze(-1) - self.offset
        return torch.exp(self.coeff * torch.pow(dist, 2))


class ExpNormalSmearing(nn.Module):
    """
    Implements exponential normal smearing of distances.

    Parameters
    ----------
    cutoff_lower : float, optional, default=0.0
        Lower bound for the smearing function.
    cutoff_upper : float, optional, default=5.0
        Upper bound for the smearing function.
    num_rbf : int, optional, default=50
        Number of radial basis functions.
    trainable : bool, optional, default=True
        If True, the parameters of smearing can be optimized.
    """

    def __init__(
        self, cutoff_lower=0.0, cutoff_upper=5.0, num_rbf=50, trainable=True
    ):
        super(ExpNormalSmearing, self).__init__()
        self.cutoff_lower = cutoff_lower
        self.cutoff_upper = cutoff_upper
        self.num_rbf = num_rbf
        self.trainable = trainable

        self.cutoff_fn = CosineCutoff(0, cutoff_upper)
        self.alpha = 5.0 / (cutoff_upper - cutoff_lower)

        means, betas = self._initial_params()
        if trainable:
            self.register_parameter("means", nn.Parameter(means))
            self.register_parameter("betas", nn.Parameter(betas))
        else:
            self.register_buffer("means", means)
            self.register_buffer("betas", betas)

    def _initial_params(self):
        # initialize means and betas according to the default values in PhysNet
        # https://pubs.acs.org/doi/10.1021/acs.jctc.9b00181
        start_value = torch.exp(
            torch.scalar_tensor(-self.cutoff_upper + self.cutoff_lower)
        )
        means = torch.linspace(start_value, 1, self.num_rbf)
        betas = torch.tensor(
            [(2 / self.num_rbf * (1 - start_value)) ** -2] * self.num_rbf
        )
        return means, betas

    def reset_parameters(self):
        means, betas = self._initial_params()
        self.means.data.copy_(means)
        self.betas.data.copy_(betas)

    def forward(self, dist):
        dist = dist.unsqueeze(-1)
        return self.cutoff_fn(dist) * torch.exp(
            -self.betas
            * (
                torch.exp(self.alpha * (-dist + self.cutoff_lower))
                - self.means
            )
            ** 2
        )


class ShiftedSoftplus(nn.Module):
    """
    Implements a shifted version of the softplus activation function.

    The output is shifted by the natural logarithm of 2.
    """

    def __init__(self):
        super(ShiftedSoftplus, self).__init__()
        self.shift = torch.log(torch.tensor(2.0)).item()

    def forward(self, x):
        """
        Applies the shifted softplus function on the input tensor.
        """
        return F.softplus(x) - self.shift


class CosineCutoff(nn.Module):
    """
    Implements the cosine cutoff function to produce a weight based on input distances.

    The weight is calculated using a cosine-based cutoff function.
    """

    def __init__(self, cutoff_lower=0.0, cutoff_upper=5.0):
        """
        Parameters
        ----------
        cutoff_lower : float, optional
            Lower bound for the cutoff, by default 0.0.
        cutoff_upper : float, optional
            Upper bound for the cutoff, by default 5.0.
        """
        super(CosineCutoff, self).__init__()
        self.cutoff_lower = cutoff_lower
        self.cutoff_upper = cutoff_upper

    def forward(self, distances):
        """
        Computes the cosine cutoff weights based on the input distances.

        Parameters
        ----------
        distances : torch.Tensor
            Tensor containing distances.

        Returns
        -------
        torch.Tensor
            Tensor containing the cosine cutoff weights.
        """
        if self.cutoff_lower > 0:
            cutoffs = 0.5 * (
                torch.cos(
                    math.pi
                    * (
                        2
                        * (distances - self.cutoff_lower)
                        / (self.cutoff_upper - self.cutoff_lower)
                        + 1.0
                    )
                )
                + 1.0
            )
            # remove contributions below the cutoff radius
            cutoffs = cutoffs * (distances < self.cutoff_upper).float()
            cutoffs = cutoffs * (distances > self.cutoff_lower).float()
            return cutoffs
        else:
            cutoffs = 0.5 * (
                torch.cos(distances * math.pi / self.cutoff_upper) + 1.0
            )
            # remove contributions beyond the cutoff radius
            cutoffs = cutoffs * (distances < self.cutoff_upper).float()
            return cutoffs


class Distance(nn.Module):
    """
    Computes distances between points in a batch and produces edge indices and weights.
    """

    def __init__(
        self,
        cutoff_lower,
        cutoff_upper,
        max_num_neighbors=32,
        return_vecs=False,
        loop=False,
    ):
        """
        Parameters
        ----------
        cutoff_lower : float
            Lower distance cutoff.
        cutoff_upper : float
            Upper distance cutoff.
        max_num_neighbors : int, optional
            Maximum number of neighbors to consider, by default 32.
        return_vecs : bool, optional
            If True, return edge vectors along with edge indices and weights, by default False.
        loop : bool, optional
            If True, include self loops, by default False.
        """
        super(Distance, self).__init__()
        self.cutoff_lower = cutoff_lower
        self.cutoff_upper = cutoff_upper
        self.max_num_neighbors = max_num_neighbors
        self.return_vecs = return_vecs
        self.loop = loop

    def forward(self, pos, batch):
        """
        Computes distances between points and returns edge indices, edge weights, and optionally edge vectors.

        Parameters
        ----------
        pos : torch.Tensor
            Tensor containing positions of points.
        batch : torch.Tensor
            Batch tensor, which assigns each node to a specific example.

        Returns
        -------
        tuple
            Tuple containing edge indices, edge weights, and optionally edge vectors.
        """
        edge_index = radius_graph(
            pos,
            r=self.cutoff_upper,
            batch=batch,
            loop=self.loop,
            max_num_neighbors=self.max_num_neighbors,
        )
        edge_vec = pos[edge_index[0]] - pos[edge_index[1]]

        if self.loop:
            # mask out self loops when computing distances because
            # the norm of 0 produces NaN gradients
            # NOTE: might influence force predictions as self loop gradients are ignored
            mask = edge_index[0] != edge_index[1]
            edge_weight = torch.zeros(edge_vec.size(0), device=edge_vec.device)
            edge_weight[mask] = torch.norm(edge_vec[mask], dim=-1)
        else:
            edge_weight = torch.norm(edge_vec, dim=-1)

        lower_mask = edge_weight >= self.cutoff_lower
        edge_index = edge_index[:, lower_mask]
        edge_weight = edge_weight[lower_mask]

        if self.return_vecs:
            edge_vec = edge_vec[lower_mask]
            return edge_index, edge_weight, edge_vec
        return edge_index, edge_weight, None


class GatedEquivariantBlock(nn.Module):
    """
    Gated Equivariant Block for tensorial properties and molecular spectra.

    This class is based on the Gated Equivariant Block defined in:
    Schütt et al. (2021): Equivariant message passing for the prediction of tensorial properties and molecular spectra.

    Parameters
    ----------
    hidden_channels : int
        Number of channels in the hidden layer.
    out_channels : int
        Number of output channels.
    intermediate_channels : int, optional
        Number of intermediate channels. If None, defaults to `hidden_channels`.
    activation : str, optional, default="silu"
        Type of activation function to use. Options include "ssp", "silu", "tanh", and "sigmoid".
    scalar_activation : bool, optional, default=False
        If True, uses scalar activation.
    """

    def __init__(
        self,
        hidden_channels,
        out_channels,
        intermediate_channels=None,
        activation="silu",
        scalar_activation=False,
    ):
        super(GatedEquivariantBlock, self).__init__()
        self.out_channels = out_channels

        if intermediate_channels is None:
            intermediate_channels = hidden_channels

        self.vec1_proj = nn.Linear(
            hidden_channels, hidden_channels, bias=False
        )
        self.vec2_proj = nn.Linear(hidden_channels, out_channels, bias=False)

        act_class = act_class_mapping[activation]
        self.update_net = nn.Sequential(
            nn.Linear(hidden_channels * 2, intermediate_channels),
            act_class(),
            nn.Linear(intermediate_channels, out_channels * 2),
        )

        self.act = act_class() if scalar_activation else None

    def reset_parameters(self):
        nn.init.xavier_uniform_(self.vec1_proj.weight)
        nn.init.xavier_uniform_(self.vec2_proj.weight)
        nn.init.xavier_uniform_(self.update_net[0].weight)
        self.update_net[0].bias.data.fill_(0)
        nn.init.xavier_uniform_(self.update_net[2].weight)
        self.update_net[2].bias.data.fill_(0)

    def forward(self, x, v):
        vec1 = torch.norm(self.vec1_proj(v), dim=-2)
        vec2 = self.vec2_proj(v)

        x = torch.cat([x, vec1], dim=-1)
        x, v = torch.split(self.update_net(x), self.out_channels, dim=-1)
        v = v.unsqueeze(1) * vec2

        if self.act is not None:
            x = self.act(x)
        return x, v


rbf_class_mapping = {"gauss": GaussianSmearing, "expnorm": ExpNormalSmearing}

act_class_mapping = {
    "ssp": ShiftedSoftplus,
    "silu": nn.SiLU,
    "tanh": nn.Tanh,
    "sigmoid": nn.Sigmoid,
}

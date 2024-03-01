"""
# Author: 
# Modified: March 1st, 2024
# ---------------------------------------
# Description:

A simple GIN (Graph Isomorphism Network) architecture modified from the torch_geometric example.
"""

import torch
import torch.nn as nn
import torch_geometric.nn as pygnn

from muben.layers import OutputLayer


class GIN(nn.Module):
    """
    Graph Isomorphism Network (GIN) model for molecular representation.

    This model uses node embeddings and processes them through GIN layers to
    derive molecular representations that can be used for various prediction tasks.
    """

    def __init__(self, config, **kwargs):
        """
        Initialize the GIN model.

        Parameters
        ----------
        n_lbs : int
            Number of possible labels.
        n_tasks : int
            Number of prediction tasks.
        max_atomic_num : int, optional, default=100
            Maximum atomic number to be used for embedding.
            This determines the embedding size for atomic types.
        d_hidden : int, optional, default=64
            Dimension of the hidden layers.
        n_layers : int, optional, default=3
            Number of GIN layers.
        uncertainty_method : str, optional, default="none"
            Method to be used for uncertainty estimation.
        dropout : float, optional, default=0.1
            Dropout rate for the GIN layers.
        """
        super().__init__()

        n_lbs = config.n_lbs
        n_tasks = config.n_tasks
        max_atomic_num = config.max_atomic_num
        n_layers = config.n_gin_layers
        d_hidden = config.d_gin_hidden
        dropout = config.dropout
        uncertainty_method = config.uncertainty_method
        task_type = config.task_type
        bbp_prior_sigma = config.bbp_prior_sigma

        self.emb = nn.Embedding(max_atomic_num, d_hidden)
        self.gnn = pygnn.GIN(d_hidden, d_hidden, n_layers, dropout=dropout, jk="cat")
        self.output_layer = OutputLayer(
            d_hidden,
            n_lbs * n_tasks,
            uncertainty_method,
            task_type=task_type,
            bbp_prior_sigma=bbp_prior_sigma,
        )

    def forward(self, batch, **kwargs) -> torch.Tensor:
        """
        Forward pass through the GIN model.

        Processes the molecular graph representation through GIN layers and produces the output logits.

        Parameters
        ----------
        batch : object
            A batch containing molecular graphs representation.
            It should have the attributes 'graphs.x', 'graphs.edge_index', and 'graphs.batch'.
        **kwargs
            Additional keyword arguments.

        Returns
        -------
        torch.Tensor
            Logits produced from the processed molecular graphs.
        """
        atoms_ids = batch.graphs.x
        edge_indices = batch.graphs.edge_index
        mol_ids = batch.graphs.batch

        embs = self.emb(atoms_ids)
        x = self.gnn(embs, edge_indices)
        x = pygnn.global_add_pool(x, mol_ids)
        logits = self.output_layer(x)

        return logits
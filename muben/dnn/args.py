"""
# Author: Anonymous
# Modified: September 22nd, 2023
# ---------------------------------------
# Description: Arguments for DNN model
"""


import logging
from typing import Optional
from dataclasses import dataclass, field
from functools import cached_property
from muben.base.args import Arguments as BaseArguments, Config as BaseConfig
from muben.utils.macro import MODEL_NAMES, FINGERPRINT_FEATURE_TYPES


logger = logging.getLogger(__name__)


@dataclass
class Arguments(BaseArguments):
    """
    Dataclass for arguments regarding the training of the DNN model.

    Inherits from BaseArguments and adds specific fields relevant to the DNN model.
    """

    # --- Model Arguments ---
    model_name: Optional[str] = field(
        default="DNN",
        metadata={"help": "Name of the model", "choices": MODEL_NAMES},
    )

    # -- Feature Arguments ---
    feature_type: Optional[str] = field(
        default="rdkit",
        metadata={
            "help": "Fingerprint generation function",
            "choices": FINGERPRINT_FEATURE_TYPES,
        },
    )

    # --- DNN Arguments ---
    n_dnn_hidden_layers: Optional[int] = field(default=8, metadata={"help": "The number of DNN hidden layers."})
    d_dnn_hidden: Optional[int] = field(
        default=128,
        metadata={"help": "The dimensionality of DNN hidden layers."},
    )


@dataclass
class Config(Arguments, BaseConfig):
    """
    Configuration dataclass for the DNN model.

    Inherits from both Arguments and BaseConfig to combine all configurations
    into a unified structure. It also calculates some properties based on
    provided arguments.
    """

    @cached_property
    def d_feature(self):
        """
        Get the dimensionality of the feature based on the feature type.

        Returns
        -------
        int
            The feature dimensionality.
        """
        if self.feature_type == "rdkit":
            return 200
        elif self.feature_type == "morgan":
            return 1024
        else:
            return 0

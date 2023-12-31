"""
# Author: Anonymous
# Modified: September 22nd, 2023
# ---------------------------------------
# Description: GIN arguments.
"""

import os.path as op
import logging
from typing import Optional
from dataclasses import dataclass, field
from muben.base.args import Arguments as BaseArguments, Config as BaseConfig
from muben.utils.macro import MODEL_NAMES

logger = logging.getLogger(__name__)


@dataclass
class Arguments(BaseArguments):
    """
    Arguments regarding the training of Neural hidden Markov Model
    """

    # --- Reload model arguments to adjust default values ---
    model_name: Optional[str] = field(
        default="GIN",
        metadata={"help": "The name of the model to be used.", "choices": MODEL_NAMES},
    )

    # --- model parameters ---
    d_gin_hidden: Optional[int] = field(default=128, metadata={"help": "Model dimensionality."})
    n_gin_layers: Optional[int] = field(default=5, metadata={"help": "The number of GIN hidden channels"})

    # --- reload training parameters ---
    lr_scheduler_type: Optional[str] = field(
        default="linear",
        metadata={
            "help": "Learning rate scheduler with warm ups defined in `transformers`, Please refer to "
            "https://huggingface.co/docs/transformers/main_classes/optimizer_schedules#schedules for details",
            "choices": [
                "linear",
                "cosine",
                "cosine_with_restarts",
                "polynomial",
                "constant",
                "constant_with_warmup",
            ],
        },
    )


@dataclass
class Config(Arguments, BaseConfig):
    # Default hyperparameters of the checkpoint, should not be changed
    embedding_dimension = 256
    max_atomic_num = 100

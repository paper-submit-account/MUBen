"""
# Author: Anonymous
# Modified: September 22nd, 2023
# ---------------------------------------
# Description: Base classes for arguments and configurations.
"""

import os
import os.path as op
import json
import torch
import logging
from typing import Optional
from dataclasses import dataclass, field, asdict
from functools import cached_property

from muben.utils.macro import MODEL_NAMES, UncertaintyMethods
from muben.utils.io import prettify_json

logger = logging.getLogger(__name__)

__all__ = ["Arguments", "Config"]


@dataclass
class Arguments:
    """
    Arguments regarding the training of Neural hidden Markov Model
    """

    # --- wandb parameters ---
    wandb_api_key: Optional[str] = field(
        default=None,
        metadata={
            "help": "The API key that indicates your wandb account suppose you want to use a user different from "
            "whom stored in the environment variables. Can be found here: https://wandb.ai/settings"
        },
    )
    wandb_project: Optional[str] = field(default=None, metadata={"help": "name of the wandb project."})
    wandb_name: Optional[str] = field(default=None, metadata={"help": "wandb model name."})
    disable_wandb: Optional[bool] = field(
        default=False,
        metadata={"help": "Disable WandB even if relevant arguments are filled."},
    )

    # --- IO arguments ---
    dataset_name: Optional[str] = field(default="", metadata={"help": "Dataset Name."})
    data_folder: Optional[str] = field(default="", metadata={"help": "The folder containing all datasets."})
    data_seed: Optional[int] = field(
        default=None,
        metadata={"help": "Seed used while constructing the random split dataset"},
    )
    result_folder: Optional[str] = field(default="./output", metadata={"help": "where to save model outputs."})
    ignore_preprocessed_dataset: Optional[bool] = field(
        default=False,
        metadata={"help": "Ignore pre-processed datasets and re-generate features if necessary."},
    )
    disable_dataset_saving: Optional[bool] = field(
        default=False, metadata={"help": "Do not save pre-processed dataset."}
    )
    disable_result_saving: Optional[bool] = field(
        default=False,
        metadata={"help": "Do not save training results and trained model checkpoints."},
    )
    overwrite_results: Optional[bool] = field(default=False, metadata={"help": "Whether overwrite existing outputs."})
    log_path: Optional[str] = field(
        default=None,
        metadata={"help": "Path to the logging file. Set to `disabled` to disable log saving."},
    )

    # --- Model Arguments ---
    model_name: Optional[str] = field(
        default="DNN",
        metadata={"help": "Name of the model", "choices": MODEL_NAMES},
    )
    dropout: Optional[float] = field(default=0.1, metadata={"help": "Dropout ratio."})
    binary_classification_with_softmax: Optional[bool] = field(
        default=False,
        metadata={
            "help": "Use softmax output instead of sigmoid for binary classification. "
            "Notice that this argument is now deprecated"
        },
    )
    regression_with_variance: Optional[bool] = field(
        default=False,
        metadata={"help": "Use two regression output heads, one for mean and the other for variance."},
    )

    # --- Training Arguments ---
    retrain_model: Optional[bool] = field(
        default=False,
        metadata={"help": "Train the model from scratch even if there are models saved in result dir"},
    )
    ignore_uncertainty_output: Optional[bool] = field(
        default=False,
        metadata={
            "help": "Ignore the saved uncertainty estimation models and results. "
            "Load model from the no-uncertainty output if possible."
        },
    )
    ignore_no_uncertainty_output: Optional[bool] = field(
        default=False,
        metadata={"help": "Ignore the model checkpoints from no-uncertainty training processes."},
    )
    batch_size: Optional[int] = field(default=32, metadata={"help": "Batch size."})
    batch_size_inference: Optional[int] = field(default=None, metadata={"help": "Inference batch size."})
    n_epochs: Optional[int] = field(default=50, metadata={"help": "How many epochs to train the model."})
    lr: Optional[float] = field(default=1e-4, metadata={"help": "Learning Rate."})
    grad_norm: Optional[float] = field(
        default=0,
        metadata={"help": "Gradient norm. Default is 0 (do not clip gradient)"},
    )
    lr_scheduler_type: Optional[str] = field(
        default="constant",
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
    warmup_ratio: Optional[float] = field(default=0.1, metadata={"help": "Learning rate scheduler warm-up ratio"})
    seed: Optional[int] = field(
        default=0,
        metadata={"help": "Random seed that will be set at the beginning of training."},
    )
    debug: Optional[bool] = field(
        default=False,
        metadata={"help": "Debugging mode with fewer training data"},
    )
    deploy: Optional[bool] = field(
        default=False,
        metadata={"help": "Deploy mode that does not throw run-time errors when bugs are encountered"},
    )
    time_training: Optional[bool] = field(
        default=False,
        metadata={"help": "Measure training time in terms of training step."},
    )
    freeze_backbone: Optional[bool] = field(
        default=False,
        metadata={
            "help": "Whether freeze the backbone model during training. "
            "If set to True, only the output layers will be updated."
        },
    )

    # --- Evaluation Arguments ---
    valid_epoch_interval: Optional[int] = field(
        default=1,
        metadata={"help": "How many training epochs within each validation step. " "Set to 0 to disable validation."},
    )
    valid_tolerance: Optional[int] = field(
        default=20,
        metadata={"help": "Maximum validation steps allowed for non-increasing model performance."},
    )
    n_test: Optional[int] = field(
        default=1,
        metadata={
            "help": "How many test loops to run in one training process. "
            "The default value for some Bayesian methods such as MC Dropout is 20."
        },
    )

    # --- Uncertainty Arguments ---
    uncertainty_method: Optional[str] = field(
        default=UncertaintyMethods.none,
        metadata={
            "help": "Uncertainty estimation method",
            "choices": UncertaintyMethods.options(),
        },
    )

    # --- Ensemble Arguments ---
    n_ensembles: Optional[int] = field(
        default=5,
        metadata={"help": "The number of ensemble models in the deep ensembles method."},
    )

    # --- SWAG Arguments ---
    swa_lr_decay: Optional[float] = field(
        default=0.5,
        metadata={"help": "The learning rate decay coefficient during SWA training."},
    )
    n_swa_epochs: Optional[int] = field(default=20, metadata={"help": "The number of SWA training epochs."})
    k_swa_checkpoints: Optional[int] = field(
        default=20,
        metadata={
            "help": "The number of SWA checkpoints for Gaussian covariance matrix. "
            "This number should not exceed `n_swa_epochs`."
        },
    )

    # --- Temperature Scaling Arguments ---
    ts_lr: Optional[float] = field(
        default=0.01,
        metadata={"help": "The learning rate to train temperature scaling parameters."},
    )
    n_ts_epochs: Optional[int] = field(
        default=20,
        metadata={"help": "The number of Temperature Scaling training epochs."},
    )

    # --- Focal Loss Arguments ---
    apply_temperature_scaling_after_focal_loss: Optional[bool] = field(
        default=False,
        metadata={"help": "Whether to apply temperature scaling after training model with focal loss."},
    )

    # --- BBP Arguments ---
    bbp_prior_sigma: Optional[float] = field(default=0.1, metadata={"help": "Sigma value for BBP prior."})

    # --- SGLD Arguments ---
    apply_preconditioned_sgld: Optional[bool] = field(
        default=False,
        metadata={"help": "Whether to apply pre-conditioned SGLD instead of the vanilla one."},
    )
    sgld_prior_sigma: Optional[float] = field(default=0.1, metadata={"help": "Variance of the SGLD Gaussian prior."})
    n_langevin_samples: Optional[int] = field(
        default=30,
        metadata={"help": "The number of model checkpoints sampled from the Langevin Dynamics."},
    )
    sgld_sampling_interval: Optional[int] = field(
        default=2,
        metadata={"help": "The number of epochs per sampling operation."},
    )

    # --- Evidential Networks Arguments ---
    evidential_reg_loss_weight: Optional[float] = field(default=1, metadata={"help": "The weight of evidential loss."})
    evidential_clx_loss_annealing_epochs: Optional[int] = field(
        default=10,
        metadata={"help": "How many epochs before evidential loss weight increase to 1."},
    )

    # --- Device Arguments ---
    no_cuda: Optional[bool] = field(
        default=False,
        metadata={"help": "Disable CUDA even when it is available."},
    )
    no_mps: Optional[bool] = field(
        default=False,
        metadata={"help": "Disable MPS even when it is available."},
    )
    num_workers: Optional[int] = field(
        default=0,
        metadata={"help": "The number of threads to process the dataset."},
    )
    num_preprocess_workers: Optional[int] = field(
        default=8,
        metadata={"help": "The number of threads to process the dataset."},
    )
    pin_memory: Optional[bool] = field(default=False, metadata={"help": "Pin memory for data loader."})
    n_feature_generating_threads: Optional[int] = field(
        default=8, metadata={"help": "Number of feature generation threads"}
    )

    def __post_init__(self):
        """
        Post initialization for creating derived attributes
        """
        if self.model_name != "DNN":
            self.feature_type = "none"
            model_name_and_feature = self.model_name
        else:
            model_name_and_feature = f"{self.model_name}-{self.feature_type}"

        # update data and result dir
        self.data_dir = op.join(self.data_folder, self.dataset_name)
        self.result_dir = op.join(
            self.result_folder,
            self.dataset_name,
            model_name_and_feature,
            self.uncertainty_method,
            f"seed-{self.seed}",
        )
        if self.data_seed is not None:
            self.data_dir = op.join(self.data_dir, f"seed-{self.data_seed}")
            self.result_dir = op.join(
                self.result_folder,
                self.dataset_name,
                f"data-seed-{self.data_seed}",
                model_name_and_feature,
                self.uncertainty_method,
                f"seed-{self.seed}",
            )

        # wandb arguments
        self.apply_wandb = not self.disable_wandb and (self.wandb_api_key or os.getenv("WANDB_API_KEY"))
        if not self.wandb_name:
            self.wandb_name = (
                f"{self.model_name}{'' if self.feature_type == 'none' else f'-{self.feature_type}'}"
                f"-{self.uncertainty_method}"
            )
        if not self.wandb_project:
            self.wandb_project = f"MUBen-{self.dataset_name}"

    @cached_property
    def device(self) -> str:
        """
        The device used by this process.
        """
        try:
            mps_available = torch.backends.mps.is_available()
        except AttributeError:
            mps_available = False

        if mps_available and not self.no_mps:
            device = "mps"
        elif self.no_cuda or not torch.cuda.is_available():
            device = "cpu"
        else:
            device = "cuda"

        return device


@dataclass
class Config(Arguments):
    # --- Dataset Arguments ---
    # The dataset attributes are to be overwritten by the dataset meta file when used
    classes = None  # all possible classification classes
    task_type = "classification"  # classification or regression
    n_tasks = None  # how many tasks (sets of labels to predict)
    eval_metric = None  # which metric for evaluating valid and test performance *during training*
    random_split = False  # whether the dataset is split randomly; False indicates scaffold split

    # --- Properties and Functions ---
    @cached_property
    def n_lbs(self):
        """
        The number of labels to predict
        """
        if self.task_type == "classification":
            if len(self.classes) == 2 and not self.uncertainty_method == UncertaintyMethods.evidential:
                return 1
            else:
                return len(self.classes)
        elif self.task_type == "regression":
            if self.uncertainty_method == UncertaintyMethods.evidential:
                return 4
            elif self.regression_with_variance:
                return 2
            else:
                return 1
        else:
            ValueError(f"Unrecognized task type: {self.task_type}")

    def __getitem__(self, item):
        if isinstance(item, str):
            return getattr(self, item)
        else:
            raise ValueError("`Config` can only be subscribed by str!")

    def get_meta(
        self,
        meta_dir: Optional[str] = None,
        meta_file_name: Optional[str] = "meta.json",
    ):
        """
        Load meta file and update attributes
        """
        if meta_dir is not None:
            meta_dir = meta_dir
        elif "data_dir" in dir(self):
            meta_dir = getattr(self, "data_dir")
        else:
            raise ValueError(
                "To automatically load meta file, please either specify "
                "the `meta_dir` argument or define a `data_dir` class attribute."
            )

        meta_dir = op.join(meta_dir, meta_file_name)
        with open(meta_dir, "r", encoding="utf-8") as f:
            meta_dict = json.load(f)

        invalid_keys = list()
        for k, v in meta_dict.items():
            if k in dir(self):
                setattr(self, k, v)
            else:
                invalid_keys.append(k)

        if invalid_keys:
            logger.warning(f"The following attributes in the meta file are not defined in config: {invalid_keys}")

        return self

    def from_args(self, args):
        """
        Initialize configuration from arguments

        Parameters
        ----------
        args: arguments (parent class)

        Returns
        -------
        self (type: BertConfig)
        """
        arg_elements = {
            attr: getattr(args, attr)
            for attr in dir(args)
            if not callable(getattr(args, attr)) and not attr.startswith("__") and not attr.startswith("_")
        }
        for attr, value in arg_elements.items():
            try:
                setattr(self, attr, value)
            except AttributeError:
                pass
        return self

    def validate(self):
        """
        Check and solve argument conflicts and throws warning if encountered any

        Returns
        -------
        self
        """

        assert not (self.model_name == "DNN" and self.feature_type == "none"), "`feature_type` is required for DNN!"

        if self.debug and self.deploy:
            logger.warning("`DEBUG` mode is not allowed when the program is in `DEPLOY`! Setting debug=False.")
            self.debug = False

        if (
            self.uncertainty_method
            in [
                UncertaintyMethods.none,
                UncertaintyMethods.ensembles,
                UncertaintyMethods.focal,
                UncertaintyMethods.temperature,
                UncertaintyMethods.evidential,
            ]
            and self.n_test > 1
        ):
            logger.warning(
                f"The specified uncertainty estimation method {self.uncertainty_method} requires "
                f"only single test run! Setting `n_test` to 1."
            )
            self.n_test = 1

        if (
            self.uncertainty_method
            in [
                UncertaintyMethods.mc_dropout,
                UncertaintyMethods.swag,
                UncertaintyMethods.bbp,
            ]
            and self.n_test == 1
        ):
            logger.warning(
                f"The specified uncertainty estimation method {self.uncertainty_method} requires "
                f"multiple test runs! Setting `n_test` to the default value 30."
            )
            self.n_test = 30

        assert not (
            self.uncertainty_method in [UncertaintyMethods.temperature, UncertaintyMethods.focal]
            and self.task_type == "regression"
        ), f"{self.uncertainty_method} is not compatible with regression tasks!"
        # temporary for evidential networks
        assert not (
            self.uncertainty_method in [UncertaintyMethods.iso] and self.task_type == "classification"
        ), f"{self.uncertainty_method} is not compatible with classification tasks!"

        if self.uncertainty_method in [
            UncertaintyMethods.focal,
            UncertaintyMethods.bbp,
            UncertaintyMethods.sgld,
            UncertaintyMethods.evidential,
        ]:
            self.ignore_no_uncertainty_output = True

        if self.k_swa_checkpoints > self.n_swa_epochs:
            logger.warning(
                "The number of SWA checkpoints should not exceeds that of SWA training epochs! "
                "Setting `k_swa_checkpoints` = `n_swa_epochs`."
            )
            self.k_swa_checkpoints = self.n_swa_epochs

        if self.uncertainty_method == UncertaintyMethods.sgld and not self.lr_scheduler_type == "constant":
            logger.warning("SGLD currently only works with constant lr scheduler. The argument will be modified")
            self.lr_scheduler_type = "constant"

        if self.uncertainty_method == UncertaintyMethods.evidential:
            self.regression_with_variance = False

        return self

    def log(self):
        """
        Log all configurations
        """
        elements = {
            attr: getattr(self, attr)
            for attr in dir(self)
            if not callable(getattr(self, attr)) and not (attr.startswith("__") or attr.startswith("_"))
        }
        logger.info(f"Configurations:\n{prettify_json(json.dumps(elements, indent=2), collapse_level=2)}")

        return self

    def save(self, file_dir: str, file_name: Optional[str] = "config"):
        """
        Save configuration to file

        Parameters
        ----------
        file_dir: file directory
        file_name: file name (suffix free)

        Returns
        -------
        self
        """
        if op.isdir(file_dir):
            file_path = op.join(file_dir, f"{file_name}.json")
        elif op.isdir(op.split(file_dir)[0]):
            file_path = file_dir
        else:
            raise FileNotFoundError(f"{file_dir} does not exist!")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.exception(f"Cannot save config file to {file_path}; " f"encountered Error {e}")
            raise e
        return self

    def load(self, file_dir: str, file_name: Optional[str] = "config"):
        """
        Load configuration from stored file

        Parameters
        ----------
        file_dir: file directory
        file_name: file name (suffix free)

        Returns
        -------
        self
        """
        if op.isdir(file_dir):
            file_path = op.join(file_dir, f"{file_name}.json")
            assert op.isfile(file_path), FileNotFoundError(f"{file_path} does not exist!")
        elif op.isfile(file_dir):
            file_path = file_dir
        else:
            raise FileNotFoundError(f"{file_dir} does not exist!")

        logger.info(f"Setting {type(self)} parameters from {file_path}.")

        with open(file_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        for attr, value in config.items():
            try:
                setattr(self, attr, value)
            except AttributeError:
                pass
        return self

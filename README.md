# MUBen: **M**olecular **U**ncertainty **Ben**mark
Code associated with paper *MUBen: Benchmarking the Uncertainty of Pre-Trained Models for Molecular Property Prediction*.

The code is built to expose implementation details as much as possible and be easily extendable.
Questions and suggestions are welcome if you find any issues while using our code.

## 0. ABOUT

MUBen is a benchmark that aims to investigate the performance of uncertainty quantification (UQ) methods built upon backbone molecular representation models.
It implements 6 backbone models (4 pre-trained and 2 non-pre-trained), 8 UQ methods (8 compatible for classification and 6 for regression), and 14 datasets from [MoleculeNet](https://moleculenet.org/) (8 for classification and 6 for regression).
We are actively expanding the benchmark to include more backbones, UQ methods and datasets.
This is an arduous task, and we welcome contribution or collaboration in any form.

### Backbones
| Backbone Models      | Paper | Official Repo | Our Implementation|
| ----------- | ----------- | ----------- | ----------- |
|*Pre-Trained Backbones* |||
| ChemBERTa |[link](https://arxiv.org/abs/2209.01712) | [link](https://github.com/seyonechithrananda/bert-loves-chemistry) | [link](https://github.com/paper-submit-account/MUBen/tree/main/muben/chemberta) | 
| GROVER   | [link](https://arxiv.org/abs/2007.02835) | [link](https://github.com/tencent-ailab/grover)| [link](https://github.com/paper-submit-account/MUBen/tree/main/muben/grover)|
|Uni-Mol| [link](https://openreview.net/forum?id=6K2RM6wVqKu) | [link](https://github.com/dptech-corp/Uni-Mol/tree/main/unimol) | [link](https://github.com/paper-submit-account/MUBen/tree/main/muben/unimol)|
|TorchMD-NET | [Architecture](https://arxiv.org/abs/2202.02541); [Pre-training](https://arxiv.org/abs/2206.00133) | [link](https://github.com/shehzaidi/pre-training-via-denoising) | [link](https://github.com/paper-submit-account/MUBen/tree/main/muben/torchmdnet)|
| *Non-Pre-Trained Backbones* |||
|DNN|-|-|[link](https://github.com/paper-submit-account/MUBen/tree/main/muben/dnn)|
|GIN| [link](https://arxiv.org/pdf/1810.00826.pdf) | [pyg](https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.nn.models.GIN.html) | [link](https://github.com/paper-submit-account/MUBen/tree/main/muben/gin)|

### Uncertainty Quantification Methods
| UQ Method | Classification | Regression | Paper |
| ----------- | ----------- | ----------- | ----------- |
| *Included* |||
| Deterministic | ✅︎ | ✅︎ | - |
| Temperature Scaling | ✅︎ | - | [link](https://arxiv.org/abs/1706.04599) |
| Focal Loss | ✅︎ | - | [link](https://arxiv.org/abs/1708.02002) |
| Deep Ensembles | ✅︎ | ✅︎ | [link](https://arxiv.org/abs/1612.01474) |
| SWAG | ✅︎ | ✅︎ | [link](https://arxiv.org/abs/1808.05326) |
| Bayes by Backprop | ✅︎ | ✅︎ | [link](https://arxiv.org/abs/1505.05424) |
| SGLD | ✅︎ | ✅︎ | [link](https://www.stats.ox.ac.uk/~teh/research/compstats/WelTeh2011a.pdf) |
| MC Dropout | ✅︎ | ✅︎ | [link](https://arxiv.org/abs/1506.02142) |

### Data

Please check [MoleculeNet](https://moleculenet.org/datasets-1) for a detailed description.
We use a subset of the MoleculeNet benckmark, including BBBP, Tox21, ToxCast, SIDER, ClinTox, BACE, MUV, HIV, ESOL, FreeSolv, Lipophilicity, QM7, QM8, QM9.

## 1. DATA

> A set of partitioned datasets are already included in this repo. You can find them under the `./data/` folder: [[scaffold split](https://github.com/paper-submit-account/MUBen/tree/main/data/files)]; [[random split](https://github.com/paper-submit-account/MUBen/tree/main/data/files-random)].

We utilize the datasets prepared by [Uni-Mol](https://github.com/dptech-corp/Uni-Mol/tree/main/unimol).
You find the data [here](https://github.com/dptech-corp/Uni-Mol/tree/main/unimol#:~:text=pockets.tar.gz-,molecular%20property,-3.506GB) or directly download it through [this link](https://bioos-hermite-beijing.tos-cn-beijing.volces.com/unimol_data/finetune/molecular_property_prediction.tar.gz).
We place the unzipped files into `./data/UniMol` by default.
For convenience, you are suggested to rename the `qm7dft`, `qm8dft`, and `qm9dft` folders to `qm7`, `qm8`, and `qm9`.

Afterwards, you can transfer the dataset format into ours by running
```bash
PYTHONPATH="." python ./assist/dataset_build_from_unimol.py
``` 
suppose you are at the project root directory.
You can specify the input (Uni-Mol) and output data directories with `--unimol_data_dir` and `--output_dir` arguments.
The script will convert *all* datasets by default (excluding PCBA).
If you want to specify a subset of datasets, you can specify the argument `--dataset_names` with the target dataset names with lowercase letters.

**Notice**: If you would like to run the Uni-Mol model, you are suggested to keep the original `UniMol` data as we will use the pre-defined molecule conformations.
Otherwise, it is safe to remove the original data.

### Other Options

If you do not want to use Uni-Mol data, you can try the scripts within the `legacy` folder, including `build_dgllife_datasets.py`, and `build_qm[7,8,9]_dataset.py`.
Notice that this may result in training/validation/test partitions different from what is being used in our experiments.

### Using Customized Datasets

If you want to test the UQ methods on your own dataset, you can use `pandas.DataFrame` structure with the following keys:
```
{
  "smiles": list of `str`,
  "labels": list of list of int/float,
  "masks": list of list of int/float (with values within {0,1})
}
```
and store them as `train.csv`, `valid.csv`, and `test.csv` files.
`mask=1` indicates the existence informative label at the position and `mask=0` indicates missing label.
You can check the prepared datasets included in our program for reference.
You are recommended to put the dataset files in the `./data/file/<dataset name>` directory, but you can of course choose your favorite location and specify the `--data_folder` argument.

The `.csv` files should be accompanied by a `meta.json` file within the same directory.
It stores some constant dataset properties, *e.g.*, `task_type` (classification or regression), `n_tasks`, or `classes` (`[0,1]` for all our classification datasets).
For the customized dataset, one **required** property is the `eval_metric` for validation and test (*e.g.*, roc-auc, rmse, *etc.*) since it is not specified in the macro file.
Please refer to `./assist/dataset_build_roe.py` for an example (unfortunately, we are not allowed to release the dataset).

## 2. REQUIREMENTS

Please find the required packages in `requirements.txt`.
Our code is developed with `Python 3.10` and does not work with Python versions earlier than `3.9`.
It is recommended to create a new `conda` environment with

```bash
conda create --name <env_name> --file requirements.txt
```

### Docker
Ulternatively, you can run this project in a docker container.
You can build your image through
```bash
docker build -t muben ./docker
```
and run your container in an interactive shell with
```bash
docker run --gpus all -it --rm  muben
```

### External Dependencies

The backbone models `GROVER` and `Uni-Mol` requires loading pre-trained model checkpoints.

- The `GROVER-base` checkpoint is available at GROVER's [project repo](https://github.com/tencent-ailab/grover) or can be directly downloaded through [this link](https://ai.tencent.com/ailab/ml/ml-data/grover-models/pretrain/grover_base.tar.gz).
Unzip the downloaded `.tar.gz` file to get the `.pt` checkpoint.
- The `Uni-Mol` checkpoint is available at Uni-Mol's [project repo](https://github.com/dptech-corp/Uni-Mol/tree/main/unimol) or can be directly downloaded through [this link](https://github.com/dptech-corp/Uni-Mol/releases/download/v0.1/mol_pre_no_h_220816.pt).

By default, the code will look for the models at locations `./models/grover_base.pt` and `./models/unimol_base.pt`, respectively.
You need to specify the `--checkpoint_path` argument if you prefer other locations and checkpoint names.

## 3. RUN

> A simple demo of running our project can be found at `./demo/demo.ipynb`.

To run each of the four backbone models with uncertainty estimation methods, you can check the `run_*.py` files in the root directory.
Example shell scripts are provided in the `./scripts` folder as `.sh` files.
You can use them through
```bash
./scripts/run_dnn_rdkit.sh <CUDA_VISIBLE_DEVICES>
```
as an example.
Notice that we need to comment out the variables `train_on_<dataset name>` in the `.sh` files to skip training on the corresponding datasets.
Setting their value to `false` **does not work**.

Another way of specifying arguments is through the `.json` scripts, for example:
```bash
PYTHONPATH="." CUDA_VISIBLE_DEVICES=0 python ./run/dnn.py ./scripts/config_dnn.json
```
This approach could be helpful for debugging the code through vscode.

To get a detailed description of each argument, you can use `--help`:
```bash
PYTHONPATH="." python ./run/dnn.py --help
```

### Logging and WandB

By default, this project uses local logging files (`*.log`) and [WandB](https://wandb.ai/site) to track training status.

The log files are stored as `./logs/<dataset>/<model>/<uncertainty>/<running_time>.log`.
You can change the file path by specifying the `--log_path` argument, or disable log saving by setting `--log_path="disabled"`.

To use WandB, you first need to register an account and sign in on your machine with `wandb login`.
If you are running your code on a public device, you can instead use program-wise signing in by specifying the `--wandb_api_key` argument while running our code.
You can find your API key in your browser here: https://wandb.ai/authorize.
To disable WandB, use `--disable_wandb [true]`.
By default, we use `MUBen-<dataset>` as WandB project name and `<model>-<uncertainty>` as the model name.
You can change this behavior by specifying the `--wandb_project` and `--wandb_name` arguments.

### Data Loading

The progress will automatically create the necessary features (molecular descriptors) required by backbone models from the SMILES strings if they are loaded properly.
The processed features are stored in the `<bottom-level data folder>/processed/` directory as `<train/valid/test>.pt` files by default, and will be automatically loaded the next time you apply the same backbone model on the same dataset.
You can change this behavior with `--disable_dataset_saving` for disabling dataset saving or `--ignore_preprocessed_dataset` for not loading from the saved (processed) dataset.

Constructing Morgan fingerprint, RDKit features or 3D conformations for Uni-Mol may take a while.
You can accelerate this process by utilizing multiple threads `--num_preprocess_workers=n>1` (default is 8).
For 3D conformations, we directly take advantage of the results from Uni-Mol but still keep the choice of generating them by ourselves if the Uni-Mol data files are not found.

### Calculating Metrics

During training, we only calculate metrics necessary for early stopping and simple prediction performance evaluation.
To get other metrics, you need to use the `./assist/results_get_metrics.py` file.

Specifically, you need to save the model predictions by **not** setting `--disable_dataset_saving`.
The results are saved as `./<result_folder>/<dataset_name>/<model_name>/<uncertainty_method>/seed-<seed>/preds/<test_idx>.pt` files.
When the training is finished, you can run the `./assist/results_get_metrics.py` file to generate all metrics for your model predictions.
For example:
```bash
PYTHONPATH="." python ./assist/results_get_metrics.py ./scripts/config_metrics.json
```
Make sure the hyper-parameters in the configuration file are updated to your need.

The metrics will be saved in the `./<result_folder>/RESULTS/<model_name>-<dataset_name>.csv` files.

### Results

We provided a more comprehensive copy of our experiment results [here](https://github.com/paper-submit-account/MUBen/tree/main/output) that are presented in the tables in our paper's appendix.
We hope it can ease some effort if you want to further analyse the behavior of our backbone models and uncertainty quantification methods. 

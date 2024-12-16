# Towards Automated Parameter Extraction from Datasets

This repository contains the code used to generate the synthetic dataset for the article  **"Towards Automated Parameter Extraction from Datasets."** 


## Abstract
The digitalization of smart manufacturing processes relies on extracting information from engineering documents. The vast amount of information is only available in natural language, and documents often exhibit complex heterogeneous layouts that machines struggle to interpret. Thus making automatic information extraction challenging. Recent AI developments may change this. We set out to evaluate the readiness of AI-based approaches for extracting information from engineering documents. In this work, we propose a general framework (MERI) for information extraction and evaluate it on a synthetic dataset explicitly created to evaluate parameter extraction on engineering documents. We find that converting documents into a machine-friendly intermediate format improves the performance of information extraction methods. However, further improvements are necessary before AI systems can extract parameters reliably.


## Installation and Setup

To set up the environment, it is recommended to use Docker for an easier installation process. The repository includes a `devcontainer.json` and a `Dockerfile` for this purpose.

### Installation Steps
1. Install dependencies:
   ```bash
   poetry install
   ```


## Running the Evaluation

### Command-Line Arguments

- `<input_document>`: (Required) The path to the content document (json).

### Options

- `--config_file_path <path>`: (Optional) Specify the path to the style configuration file. Default is `scripts/configs/styles.yaml`.
- `--outdir <directory>`: (Optional) Specify the output directory where results will be saved. Default is `output`.
- `--tasks <task_list>`: (Optional) Specify the tasks to perform, e.g., `text_paragraph`. Default is `all`.


### Example
```bash
python python scripts/gen_dataset.py example_document --config_file_path scripts/configs/styles.yaml --outdir output
```

## Acknowledgments
This work was done in the Business Finland funded project [Virtual Sea Trial](https://virtualseatrial.fi/).


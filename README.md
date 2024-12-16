# Towards Automated Parameter Extraction from Datasets

This repository contains the code used to generate the synthetic dataset for the article  [**"Towards Automated Parameter Extraction from Datasets."**](https://github.com/Novia-RDI-Seafaring/auto-param-extraction)


## Abstract
The digitalization of smart manufacturing processes relies on extracting information from engineering documents. These documents often exhibit complex heterogeneous layouts that machines struggle to interpret. Recent AI developments may change this. We set out to evaluate the readiness of AI-based approaches for extracting information from engineering documents. In this work, we propose a general framework (MERI) for information extraction and evaluate it on a synthetic dataset explicitly created to evaluate parameter extraction from engineering documents. We find that converting documents into a machine-friendly intermediate format improves the performance of information extraction methods. However, further improvements are necessary before AI systems can extract parameters reliably.


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

## How the Generation Works

The generation process involves creating different style variations of the same content based on the provided content document and styling configuration. Here's a detailed explanation:

1. **Content Document**: Located in `source_data/<document>/`, this JSON document contains the base content that will be styled in various ways. It includes sections, headings, lists, and other elements that form the structure of the document.

2. **Styling Configuration**: The configuration file, typically a YAML file, defines various style options that can be applied to the content. This includes font sizes, colors, and layout options. An example can be found in `scripts/configs/style_config.yaml`

3. **Parameter Extraction Tasks**: In the `gt_info` file in `source_data/<document>/`, different parameter extraction tasks are defined. These tasks are linked to elements in the content document and include ground truth (GT) annotations. The tasks specify what parameters need to be extracted and how they relate to the content.

4. **Synthetic Dataset Generation**: Using the content document and styling configuration, the system generates a synthetic dataset. This dataset includes multiple styled versions of the content, each with GT annotations for parameter extraction. The variations help in training and evaluating AI models for parameter extraction tasks.

5. **Headless Browser for Rendering**: To generate styled content, the system uses a headless browser. This allows for rendering HTML and CSS to create realistic document layouts, which are then used to produce the synthetic dataset.

## Acknowledgments
This work was done in the Business Finland funded project [Virtual Sea Trial](https://virtualseatrial.fi/).


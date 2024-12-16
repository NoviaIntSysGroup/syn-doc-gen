import argparse
import os
import yaml
from itertools import product

def parse_args():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('datasheet_name', type=str, help='Path to the JSON file containing the data.')
    parser.add_argument('--config_file_path', type=str, required=True)
    parser.add_argument('--tasks', type=str, nargs="+", help='Tasks to run. If None all tasks are run, else pass space delimited list.', default=None)
    parser.add_argument('--outdir', type=str, help='Name of output directory.', default="output")

    # Parse the argument
    args = parser.parse_args()

    return args

def compute_font_size_dict(paragraph_size={"from": 10, "to": 10}):

    p_from = paragraph_size["from"]
    p_tp = paragraph_size["to"]

    return {
        "heading1_font_size": {'from': p_tp+12, 'to': p_tp+12},
        "heading2_font_size": {'from': p_tp+8, 'to': p_tp+8},
        "heading3_font_size": {'from': p_tp+4, 'to': p_tp+4},
        "paragraph_font_size": {'from': p_from, 'to': p_tp},
        "small_font_size": {'from': p_from-4, 'to': p_from-4},
    }
    

def load_config(config_file_path: str):

    assert os.path.exists(config_file_path)

    with open(config_file_path, 'r') as file:
        config = yaml.safe_load(file)

    
    elements = []
    options= []
    for layout_element in config["styles"]:
        for key, value in layout_element.items():
            elements.append(key)
            options.append(value)

    config_overwrite_list = []
    for comb in product(*options):
        config_overwrite = {}
        assert len(comb) == len(elements)
        for style_key, style_value in zip(elements, comb):
            if isinstance(style_value, dict):
                config_overwrite[style_key] = style_value
            else:
                config_overwrite[style_key] = [style_value]

        if "paragraph_font_size" in config_overwrite.keys():
            config_overwrite.update(compute_font_size_dict(config_overwrite["paragraph_font_size"]))

        
        config_overwrite_list.append(config_overwrite)


    return config_overwrite_list
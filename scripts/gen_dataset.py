import argparse
import json, os
import tqdm
import sys

base_dir = os.path.abspath(os.path.join("__file__", ".."))
sys.path.append(base_dir)
from dataset_generator.generator import ParamExtractionSampleGenerator
from dataset_generator.datamodels import Task
from configs.eval_opts import parse_args, load_config
import copy

# if not set, default is used
config_overwrite = {
    "column_classes": ["one-column", "two-columns"],
    "list_classes": ['list-style-1'],
    "table_border_classes": ['no-borders'], #['no-borders', 'underline-first-row', 'grid-border']
    "table_classes": ['full-width', 'narrow-center'],
    "table_color_classes": ['colorize-first-row', 'transparent-first-row'],
    "heading_fonts": ["Inter"],
    "body_fonts":  ["Roboto"],
    "line_height_size": {'from': 1.0, 'to': 1.05, "step":0.05},
    "heading1_font_size": {'from': 24, 'to': 24},
    "heading2_font_size": {'from': 18, 'to': 18},
    "heading3_font_size": {'from': 14, 'to': 14},
    "paragraph_font_size": {'from': 12, 'to': 12},
    "small_font_size": {'from': 8, 'to': 8},
    "image_max_width": [50, 100]
}

# EXAMPLE:
# python scripts/gen_dataset.py AlfaLavalT8 text_paragraph text_list  --seeds 1 2
# python scripts/gen_dataset.py AlfaLavalT8 --seeds 2 3 4

if __name__ == "__main__":
    #args = parser.parse_args()
    #args.config_file_path

    args = parse_args()
    print(args)

    out_dir = f"{base_dir}/{args.outdir}"
    schema_template = f"{base_dir}/source_data/schema_template.json"

    datasheet_path = os.path.join(f"{base_dir}/source_data", args.datasheet_name)
    doc_content_path = os.path.join(datasheet_path, "doc_content.json")
    gt_info_path = os.path.join(datasheet_path, "gt_info.json")

    datasheet_name = args.datasheet_name

    # run all tasks if no specific is provided
    if args.tasks is None:
        with open(gt_info_path) as f:
            gt_info = json.load(f)
        
        tasks = list(gt_info.keys()) + ["unitConversion"]
    else:
        tasks = args.tasks

    style_config = load_config(args.config_file_path)
    print(f"Registered {len(style_config)} different styles.")
    for task in tqdm.tqdm(tasks):
        for i, style in enumerate(style_config):
            current_overwrite_config = copy.deepcopy(config_overwrite)
            current_overwrite_config.update(style)

            print(f"Task: {task} style: {current_overwrite_config}")

            sample_generator = ParamExtractionSampleGenerator(datasheet_name,
                                                            Task(task),
                                                            seed=i, # only for id when fixing the style
                                                            pdf_overwrite_styles=current_overwrite_config,
                                                            doc_content_json_path=doc_content_path,
                                                            gt_info_dict_path=gt_info_path,
                                                            schema_template_path=schema_template)
            
            sample_generator.generate(out_dir=out_dir)
       
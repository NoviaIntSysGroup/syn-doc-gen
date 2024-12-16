import json
from dataclasses import dataclass, asdict, field
from jsonpath_ng.jsonpath import DatumInContext
from jsonpath_ng import parse
from typing import Union, List, Tuple, Dict
import os
import tempfile
import shutil
from syntetic_pdf_generator.PDFGeneratorHTMLCSSJS import PDFGeneratorHTMLCSSJS
import glob
import tqdm
from .datamodels import *

import hashlib

def dict_to_id(d):
    # Serialize the dictionary into a JSON string, sorting keys to ensure consistency
    serialized = json.dumps(d, sort_keys=True)
    # Compute the hash of the serialized string
    return hashlib.sha256(serialized.encode()).hexdigest()

        
        
class ParameterJsonSchema:
    """ Class to add parameters to json schema
    
    Schema has always properties.
    properties: {PARAMKEY: {param value}}
    """

    def __init__(self, schema_template_path = "schema_template.json") -> None:
        with open(schema_template_path) as f:
            self.schema = json.load(f)

    def add_single_parameter(self, schema_param: SchemaParameter):
        key, value = schema_param.json_schema_property()
        self.schema["properties"][key] = value
    
    def add_parameters(self, schema_params: list[SchemaParameter]):
        for param in schema_params:
            self.add_single_parameter(param)
    
    def get_parameter_keys(self):

        return list(self.schema["properties"].keys())

    def save_schema_to_json(self, file_path: str):
        """
        Save the schema to a JSON file.

        :param file_path: The path where the JSON file will be saved.
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as json_file:
                json.dump(self.schema, json_file, ensure_ascii=False, indent=4)
            print(f"Schema successfully saved to {file_path}")
        except Exception as e:
            print(f"An error occurred while saving the schema: {e}") 

class JsonParamDoc:
    def __init__(self) -> None:
        self.json_param_doc = {}    

    def add_single_parameter(self, param_value: ParameterProperties, key: str):
        self.json_param_doc[key] = param_value.dict_value()

    def save_schema_to_json(self, file_path: str):
        """
        Save the schema to a JSON file.

        :param file_path: The path where the JSON file will be saved.
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as json_file:
                json.dump(self.json_param_doc, json_file, ensure_ascii=False, indent=4)
            print(f"Schema successfully saved to {file_path}")
        except Exception as e:
            print(f"An error occurred while saving the schema: {e}") 

class ParamExtractionSampleGenerator:

    def __init__(self, datasheetname: str, task: Task, doc_content_json_path: str, pdf_overwrite_styles: dict = {},
                 seed=1, gt_info_dict_path: str = "gt_info.json", schema_template_path="schema_template.json") -> None:
        
        with open(gt_info_dict_path) as f:
            self.gt_info_dict = json.load(f)

        with open(doc_content_json_path, 'r', encoding='utf-8') as f:
            self.doc_content = json.load(f)

        self.datasheetname = datasheetname

        self.task = task

        self.schema_template_path = schema_template_path

        self.json_schema: ParameterJsonSchema = None
        self.json_gt: JsonParamDoc = None

        self.seed = seed # only for pdf generation
        self.temp_dir = tempfile.TemporaryDirectory()

        self.pdf_overwrite_styles = pdf_overwrite_styles

    def build_param_info(self, pdf_json_path):
        self.params_info = self.task.build_param_info(self.gt_info_dict, pdf_json_path)

    def generate_pdf(self):
    
        output_file = os.path.join(self.temp_dir.name, f"{self.id}.pdf")
        generator = PDFGeneratorHTMLCSSJS(self.doc_content, output_file)
        generator.generate_pdf(seed=self.seed, config_overwrite = self.pdf_overwrite_styles)

        return output_file
        
    def generate_schema_and_gt(self):
        generated_json_schema = ParameterJsonSchema(self.schema_template_path)
        generated_json_gt = JsonParamDoc()
        
        for p_info in self.params_info:
            generated_json_schema.add_single_parameter(schema_param=p_info["schema"])
            generated_json_gt.add_single_parameter(p_info["gt_props"], p_info["param_key"])

        self.json_schema = generated_json_schema
        self.json_gt = generated_json_gt
    
    def generate(self, out_dir):
        pdf_output_file = self.generate_pdf()
        self.build_param_info(f"{pdf_output_file}.json")
        self.generate_schema_and_gt()
        res_dir = self.save(out_dir)
        print(f"Stored at {res_dir}")

    @property
    def id(self):
        style_uuid = dict_to_id(self.pdf_overwrite_styles)
        return f"{self.datasheetname}_{self.task.source_modality}_{self.seed}_{style_uuid}"

    @property
    def info(self):
        return {
            "task": self.task.source_modality,
            "datasheet_name": self.datasheetname,
            "seed": self.seed,
            "gt_info": self.gt_info_dict,
            "doc_content": self.doc_content
        }


    def save(self, out_dir):
        target_dir = os.path.join(out_dir, self.id)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
        
        self.json_schema.save_schema_to_json(os.path.join(target_dir, "schema.json"))
        self.json_gt.save_schema_to_json(os.path.join(target_dir, "gt_value.json"))

        with open(os.path.join(target_dir, "info.json"), 'w', encoding='utf-8') as info_file:
            json.dump(self.info, info_file, ensure_ascii=False, indent=4)

        with open(os.path.join(target_dir, "pdf_style_overwrite.json"), 'w', encoding='utf-8') as pdf_style_file:
            json.dump(self.pdf_overwrite_styles, pdf_style_file, ensure_ascii=False, indent=4)  # Save the PDF style overwrite settings

        shutil.copytree(self.temp_dir.name, target_dir, dirs_exist_ok =True)

        return target_dir

if __name__ == "__main__":

    # set these parameters
    
    datasheet_name = "AlfaLavalT8"
    task = Task("text_paragraph")
    run_seeds = [1,2,3]

    ###############

    out_dir = "/workspaces/syntetic-pdf-generation/output"
    schema_template = "/workspaces/syntetic-pdf-generation/source_data/schema_template.json"

    datasheet_path = os.path.join("/workspaces/syntetic-pdf-generation/source_data", datasheet_name)
    doc_content_path = os.path.join(datasheet_path, "doc_content.json")
    gt_info_path = os.path.join(datasheet_path, "gt_info.json")
    
    for seed in tqdm.tqdm(run_seeds):
        sample_generator = ParamExtractionSampleGenerator(datasheet_name,
                                                        task, 
                                                        seed=seed,
                                                        doc_content_json_path=doc_content_path,
                                                        gt_info_dict_path=gt_info_path,
                                                        schema_template_path=schema_template)
        
        sample_generator.generate(out_dir=out_dir)
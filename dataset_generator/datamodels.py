from dataclasses import dataclass, asdict, field
from jsonpath_ng.jsonpath import DatumInContext
from jsonpath_ng import parse
from typing import Union, List, Tuple, Dict
from syntetic_pdf_generator.PDFGeneratorHTMLCSSJS import PDFGeneratorHTMLCSSJS
from jsonpath_ng.ext import parse as parse_ext
import json


class PDFContentManager:

    def __init__(self, pdf_json_path: str) -> None:

        with open(pdf_json_path) as f:
            self.pdf_content = json.load(f)
    
    def get_location(self, content_ids):
        result = {
            "bboxes": [],
            "pageIndexes": []
        }

        for content_id in content_ids:
            if isinstance(content_id, int) or isinstance(content_id, float):
                content_id = str(content_id)

            jsonpath_expr = parse_ext("$..content_id")
            
            matches = [match for match in jsonpath_expr.find(self.pdf_content) if match.value == content_id]
            assert len(matches) == 1

            result["bboxes"].append(matches[0].context.value["bounding_box"]["xyxy"])
            if matches[0].context.value["page_number"] not in result["pageIndexes"]:
                result["pageIndexes"].append(matches[0].context.value["page_number"] - 1) # idx starts counting at 0
            
        return result
    
@dataclass
class SchemaParameter:
    label: str
    description: str
    type: str
    desiredUnit: str
    key: str

    def json_schema_property(self):
        value = {
                "label": self.label,
                "description": f"{self.description}. Desired unit: {self.desiredUnit}.",
                #"desiredUnit": self.desiredUnit,
                "type": self.type,
                "properties": {"parameter_properties": {"$ref": "#/definitions/parameter_properties"}},
                "additionalProperties": False,
                "required": ["parameter_properties"]
            }
        return (self.key, value)

@dataclass
class ParameterProperties:
    value: Union[float, int, None]
    unit: Union[str, None]
    bboxes: List[List[Union[float, int]]] = field(default_factory=lambda: [[0.0, 0.0, 0.0, 0.0]])
    pageIndexes: List[int] = field(default_factory=lambda: [0])

    def dict_value(self):
        return {
            "parameter_properties": asdict(self)
        }

@dataclass
class Task:
    source_modality: str

    def jsonpath_gt_info_query(self):
        """ Returns jsonpath query for all relevant parameters defined in gt_json
        """
        if self.source_modality == "unitConversion":
            query = '$.*[*]'
        else:
            query = f"$.{self.source_modality}[*]"
        return query
    
    def build_param_info(self, gt_info_dict, pdf_json_path):
        print("PDF JSON PATH:", pdf_json_path)
        pdfContentManager = PDFContentManager(pdf_json_path)
        # creates parameters of interest as list of dicts
        
        query = self.jsonpath_gt_info_query()
        jsonpath_expr = parse(query)

        task_parameters: list[DatumInContext] = jsonpath_expr.find(gt_info_dict)

        if self.source_modality == "unitConversion":
            task_parameters = [task for task in task_parameters if "unitConversion" in task.value.keys()]

        gt_params_info = []
        for param in task_parameters:
            schemaInfo = param.value["schemaInfo"]
            gt_value = param.value["gt_value"]

            if self.source_modality == "unitConversion":
                schemaInfo.update(param.value[self.source_modality]["schemaInfo_update"])
                gt_value.update(param.value[self.source_modality]["adj_gt"])


            content_ids = param.value["content_refs"]
            locations = pdfContentManager.get_location(content_ids)

            gt_info = {
                    "param_key": param.value["paramKey"],
                    "schema": SchemaParameter(**param.value["schemaInfo"], key=param.value["paramKey"]),
                    "gt_props": ParameterProperties(**param.value["gt_value"], **locations)
                }

            gt_params_info.append(
                gt_info
            )
            
        return gt_params_info


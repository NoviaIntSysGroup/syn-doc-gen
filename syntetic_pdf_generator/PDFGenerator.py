import json
import pdfkit  # For HTML/CSS to PDF conversion
from fpdf import FPDF  # For direct Python to PDF
from pylatex import Document, Section, Subsection, Command, Table, Tabular, Figure, Itemize, NoEscape  # Import NoEscape
from docx import Document as DocxDocument  # For Word document creation
import xlsxwriter  # For XLSX creation
import os

class PDFGeneratorBase:
    def __init__(self, json_data, output_path):
        self.data = json_data
        self.output_path = output_path

    def generate_pdf(self):
        # Default implementation using direct PDF generation
        pdf = FPDF()
        pdf.add_page()
        # Load the font
        sans_font_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'fonts', 'ttf', 'DejaVuSans.ttf')
        serif_font_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'fonts', 'ttf', 'DejaVuSerif.ttf')
        pdf.add_font('DejaVuSans', '', sans_font_path, uni=True)  # Add DejaVuSans font with UTF-8 support
        pdf.add_font('DejaVuSerif', '', serif_font_path, uni=True)  # Add DejaVuSans font with UTF-8 support
        pdf.set_font('DejaVuSerif', size=12)  # Use the new font
        pdf.cell(200, 10, txt=self.data.get('title', 'Generated PDFffff'), ln=True, align='C')

        for section in self.data.get('sections', []):
            pdf.set_font('DejaVuSerif', size=12)
            pdf.cell(200, 10, txt=section.get('header', ''), ln=True)
            content = section.get('content', '')
            if isinstance(content, dict):
                if 'variables' in content:
                    pdf.set_font("DejaVuSans", size=12)
                    pdf.cell(0, 10, 'Variables:', ln=True)
                    for var, desc in content['variables'].items():
                        pdf.cell(0, 10, f"{var}: {desc}", ln=True)
                elif 'table' in content:
                    pdf.set_font("DejaVuSans", size=12)
                    for header in content['table']['headers']:
                        pdf.cell(40, 10, header, border=1)
                    pdf.ln()
                    for row in content['table']['rows']:
                        for cell in row:
                            pdf.cell(40, 10, cell, border=1)
                        pdf.ln()
                elif 'images' in content:
                    for img in content['images']:
                        pdf.image(img['src'], w=100)  # Adjust width as needed
                        pdf.cell(0, 10, img['caption'], ln=True)
            else:
                pdf.multi_cell(0, 10, content)

        pdf.output(self.output_path)


class PDFGeneratorLatex(PDFGeneratorBase):
    def generate_pdf(self):
        doc = Document()
        doc.preamble.append(Command('title', self.data.get('title', 'Generated fffPDF')))
        doc.preamble.append(Command('author', 'PDF Generator'))
        doc.preamble.append(Command('date', NoEscape(r'\today')))
        doc.append(NoEscape(r'\maketitle'))

        # Ensure to include the graphicx package
        doc.preamble.append(Command('usepackage', 'graphicx'))

        for section in self.data.get('content', []):
            if section['type'] == 'section':
                with doc.create(Subsection(section.get('title', ''))):
                    for element in section.get('elements', []):
                        if element['type'] == 'text':
                            doc.append(element['content'])
                        elif element['type'] == 'list':
                            with doc.create(Itemize()) as itemize:
                                for item in element['content']:
                                    itemize.add_item(item)
                        elif element['type'] == 'image':
                            doc.append(NoEscape(r'\includegraphics{' + element['content'] + '}'))

        doc.generate_pdf(self.output_path.replace(".pdf", ""), clean_tex=False)



 


# Example usage
if __name__ == "__main__":
    json_data = {
        "title": "Benchmark PDF for AI Model Evaluation",
        "sections": [
            {"header": "Introduction", "content": "This document serves as a benchmark for evaluating AI models on their ability to extract data from PDFs."},
            {"header": "Heat Exchanger Overview", "content": "A heat exchanger is a device that transfers heat between two or more fluids."},
            {"header": "Key Variables", "content": {"variables": {"Q": "Heat transfer rate (W)", "U": "Overall heat transfer coefficient (W/m²·K)", "A": "Heat transfer area (m²)", "ΔT": "Temperature difference (K)"}}},
            {"header": "Tables", "content": {"table": {"headers": ["Variable", "Description"], "rows": [["Q", "Heat transfer rate"], ["U", "Overall heat transfer coefficient"], ["A", "Heat transfer area"], ["ΔT", "Temperature difference"]]}}},
            {"header": "Images", "content": {"images": [{"src": "images/heat_exchanger_diagram.png", "caption": "Diagram of a heat exchanger"}]}},
            {"header": "Derived Content", "content": "The heat transfer rate can be calculated using the formula Q = U * A * ΔT."}
        ]
    }


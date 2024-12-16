from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException  # Add this import

from bs4 import BeautifulSoup  # Import BeautifulSoup
from .PDFGenerator import PDFGeneratorBase
import time
import os
import pdfkit
import http.server
import socketserver
import threading
import uuid  # Import uuid for generating unique IDs
import base64
import json
import io  # Import io for BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfReader, PdfWriter

class PDFGeneratorHTMLCSSJS(PDFGeneratorBase):

    def generate_pdf(self, seed=1, config_overwrite={}, css_vars=None, additional_css=None):
        # Add IDs to the elements in self.data['content']
        element_ids = {}  # Dictionary to store element IDs

        for section in self.data.get('content', []):
            if section['type'] == 'heading':
                for element in section['content']:
                    element_id = str(uuid.uuid4())
                    element['id'] = element_id
                    element_ids[element_id] = element
            elif section['type'] == 'section':
                for element in section.get('content', []):
                    element_id = str(uuid.uuid4())
                    element['id'] = element_id
                    element_ids[element_id] = element
                    if element['type'] == 'table':
                        for i, item in enumerate(element['content']):
                            item['id'] = str(uuid.uuid4())
                            item['type'] = 'table-cell'
                            if element['content'][i].get('col_header', False):
                                item['type'] = 'col-header'
                            if element['content'][i].get('row_header', False):
                                item['type'] = 'row-header'
                    if element['type'] == 'list':
                        for i, item in enumerate(element['content']):
                            if isinstance(item, str):
                                text = item
                                element['content'][i] = {
                                    'content': text,
                                    'type': 'list-item',
                                    'id': str(uuid.uuid4())
                                }
                            elif isinstance(item, dict):
                                item['id'] = str(uuid.uuid4())

                            #item_id = str(uuid.uuid4())
                            #element['content'][i]['id'] = item_id
                            #element_ids[item_id] = element['content'][i]
                            

        # Convert the modified self.data['content'] to JSON
        with open('static/markup.html', 'r', encoding='utf-8') as file:
            html_content = file.read()

        html_content = html_content.replace("´", "\´")


        # Save HTML content to a temporary file
        temp_html_path = os.path.abspath(self.output_path.replace('.pdf', '.tmp.html'))
        os.makedirs(os.path.dirname(temp_html_path), exist_ok=True)
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            html_content = html_content.replace('JSON_DATA', json.dumps(self.data))
            html_content = html_content.replace('CONFIG_OVERWRITE', json.dumps(config_overwrite))
            html_content = html_content.replace('MY_SEED', str(seed))
            if css_vars:
                html_content = html_content.replace('/* REPLACE THIS FOR VARIABLE OVERRIDES */', css_vars)
            if additional_css:
                html_content = html_content.replace('/* REPLACE THIS FOR STYLE OVERRIDES */', additional_css)
            f.write(html_content)

        print(f"HTML content saved to {temp_html_path}")

        print("Creating ChromeDriver instance")

        chrome_options = Options()  # Create an instance of Options
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--print-to-pdf-no-header')
        chrome_options.add_argument('--kiosk-printing')
        chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
        chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
        chrome_options.add_argument("start-maximized")  # Start maximized
        chrome_options.add_argument("disable-infobars")  # Disable infobars
        chrome_options.add_argument("--disable-extensions")  # Disable extensions
        chrome_options.add_argument("--disable-popup-blocking")  # Disable popup blocking
        chrome_options.add_argument("--disable-search-engine-choice-screen")  # Disable the modal for choosing default search engine...
        chrome_options.add_argument("--enable-local-file-access")
        chrome_options.add_argument("--force-device-scale-factor=1")  # Set device scale factor to 1
        chrome_options.add_argument("--window-size=2480,3508")  # Set window size to A4 dimensions in pixels (300 DPI)
        chrome_options.add_argument("--enable-logging")  # Enable logging
        chrome_options.add_argument("--v=3")  # Set logging level

        chrome_options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

        try:
            # Force redownload by setting cache_valid_range in the install method
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(f"file://{temp_html_path}")

            # Wait for the page to load and the element to be available
            WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.ID, "page1"))
            )

            # Capture console logs
            for entry in driver.get_log('browser'):
                try:
                    print(entry["message"].split('"')[1])
                except:
                    print(entry)
                

            # Execute JavaScript to get the bounding box of the element
            bounding_box = driver.execute_script("""
                return document.querySelector('#page1').getBoundingClientRect();
            """)
            print("bounding_box: ", bounding_box)

            #print(f"Bounding box: {bounding_box}")

            # Save the PDF
            driver.execute_script('window.print();')

        except TimeoutException:
            print("Timeout while waiting for the page to load.")
        finally:
            #driver.quit()
            print("go ahead")
            #while True:
            #    time.sleep(1)
        print("PDF generation completed.")

        # Print to PDF
        print_options = {
            'paperWidth': 8.27,  # A4 width in inches
            'paperHeight': 11.69,  # A4 height in inches
            'marginTop': 0,
            'marginBottom': 0,
            'marginLeft': 0,
            'marginRight': 0,
            'printBackground': True
        }

        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(f"file://{temp_html_path}")

            # Emulate print media
            driver.execute_script('document.body.style.zoom="100%"')
            driver.execute_cdp_cmd('Emulation.setEmulatedMedia', {'media': 'print'})

            time.sleep(10)  # Increase wait time to 5 seconds
            # Extract positions and bounding boxes
            # wait = WebDriverWait(driver, 1)  # Decrease timeout to 1 second
            # for element_id, element in element_ids.items():
            #    #print(f"Looking for element with ID: {element_id}")
            #    try:
            #        web_element = wait.until(EC.presence_of_element_located((By.ID, element_id)))
            #        bounding_box = driver.execute_script("""
            #            var rect = arguments[0].getBoundingClientRect();
            #            return {x: rect.left, y: rect.top, width: rect.width, height: rect.height};
            #        """, web_element)
            #        page_number = 1  # Assuming single-page PDF for simplicity#
            #
            #        # Update the element with bounding box and page number
            #        element['bounding_box'] = bounding_box
            #        element['page_number'] = page_number
            #    except TimeoutException:
            #        print(f"Timeout: Element with ID {element_id} not found.")
            #        continue

            # Get window content as JSON
            window_content = driver.execute_script("""
                return JSON.stringify(window.json_data);
            """)

            # Process the window content JSON
            json_data = json.loads(window_content)
            
            print(json_data.keys())
            #print(type(json_data))
            #for element_id, element in element_ids.items():
            #    if element_id in window_content_data:
            #        element.update(window_content_data[element_id])

            def remove_ids(data):
                if isinstance(data, dict):
                    data.pop('id', None)
                    for key, value in data.items():
                        remove_ids(value)
                elif isinstance(data, list):
                    for item in data:
                        remove_ids(item)
        
            def coord_pdf2web(bbox):
                # Convert coordinates from PDF to web
                return {
                    'x': round(bbox['x'] / (A4[0] / 100), 2),  # Convert x
                    'y': round(100 - (bbox['y'] + bbox['height'] / (A4[1] / 100)), 2),  # Convert y
                    'width': round(bbox['width'] / (A4[0] / 100), 2),  # Convert width
                    'height': round(bbox['height'] / (A4[1] / 100), 2)  # Convert height
                }
            
            def transform_coordinates_to_top_left(xyxy, page_height):
                """
                Transforms coordinates from bottom-left to top-left coordinate system.

                Parameters:
                xyxy (tuple): A tuple containing (x_min, y_min, x_max, y_max) in bottom-left coordinates.
                page_height (float): The height of the page.

                Returns:
                tuple: A tuple containing (x_min, y_min, x_max, y_max) in top-left coordinates.
                """
                x_min, y_min, x_max, y_max = xyxy
                
                # Transform y-coordinates
                new_y_min = page_height - y_max
                new_y_max = page_height - y_min
                
                return (x_min, new_y_min, x_max, new_y_max)
            
            def coord_web2pdf(bbox):
                
                x = round(bbox['x'] * (A4[0] / 100), 2)  # Convert x
                y = round((100 - bbox['y']) * (A4[1] / 100) - bbox['height'] * (A4[1] / 100), 2)  # Convert y
                width = round(bbox['width'] * (A4[0] / 100), 2)  # Convert width
                height = round(bbox['height'] * (A4[1] / 100), 2)  # Convert height

                # Calculate x_max and y_max
                x_max = x + width
                y_max = y + height
                xyxy_coordinates = transform_coordinates_to_top_left([x, y, x_max, y_max],  A4[1])

                # Convert coordinates from web to PDF
                return {
                    'x': x,  # Convert x
                    'y': y,  # Convert y
                    'width': width,  # Convert width
                    'height': height,  # Convert height
                    'xyxy': xyxy_coordinates # topleft coordinate system
                }
            

            
            def change_coordinate_system(data, system='pdf'):
                if system == 'pdf':
                    fn = coord_web2pdf
                elif system == 'web':
                    fn = coord_pdf2web
                else:
                    return

                # Iterate through the elements and convert coordinates
                for element in data.get('content', []):
                    if 'bounding_box' in element:
                        bbox = element['bounding_box']
                        # Convert coordinates from web to PDF
                        element['bounding_box'] = fn(bbox)
                    if 'content' in element:
                        change_coordinate_system(element, system=system)  # Recursively process nested elements

            
            change_coordinate_system(json_data, 'pdf')

            # Save the JSON content to a file
            # Deep copy the JSON data before modifying it and remove ids.
            json_data_copy = json.loads(json.dumps(json_data))


            remove_ids(json_data_copy)
            with open(self.output_path.replace('.pdf', '.pdf.json'), 'w') as json_file:
                json.dump(json_data_copy, json_file, indent=4)

            # Print to PDF
            result = driver.execute_cdp_cmd("Page.printToPDF", print_options)
            output_dir = os.path.dirname(self.output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            with open(self.output_path, 'wb') as pdf_file:
                pdf_file.write(base64.b64decode(result['data']))

            colors = json.loads(driver.execute_script("""
                return JSON.stringify(window.colors);
            """))

        finally:
            print("... done")
            #while True:
            #    foo=1
            #driver.quit()

        # Validate bounding boxes and draw them on the PDF
        def draw_bounding_boxes(input_pdf_path, output_pdf_path, json_data, colors):
            input_pdf = PdfReader(input_pdf_path)
            output_pdf = PdfWriter()

            margin = 0  # No margin
            dpi = 96  # Set both screen and PDF DPI to 96

            for page_num in range(len(input_pdf.pages)):
                print(f"Processing page {page_num + 1}")  # Debugging: Log current page number
                page = input_pdf.pages[page_num]
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=A4)

                # Process elements for the current page
                process_elements(json_data.get('content', []), can, page_num, colors, dpi, margin, A4[1])

                can.save()  # Save the canvas to finalize drawing

                packet.seek(0)
                new_pdf = PdfReader(packet)

                # Ensure new_pdf contains pages and merge each page
                for new_page_num in range(len(new_pdf.pages)):
                    page.merge_page(new_pdf.pages[new_page_num])
                output_pdf.add_page(page)

            with open(output_pdf_path, "wb") as outputStream:
                output_pdf.write(outputStream)
        draw_bounding_boxes(self.output_path, self.output_path.replace('.pdf', '_bbox.pdf'), json_data, colors)

# TODO:
# - we can add all elements one item at a time with javascript in the browser, and then we can detect if it shall be put on the next page or not.

def draw_bbox(can, bbox, color, dpi, margin, page_height, element):
    can.setStrokeColor(color)
    can.setLineWidth(2)
    x = bbox['x']#float(bbox['x']) / 100 * A4[0] + margin
    y = bbox['y']#page_height - (float(bbox['y']) / 100 * page_height) - (float(bbox['height']) / 100 * page_height)
    width = bbox['width']#float(bbox['width']) / 100 * A4[0]
    height = bbox['height']#float(bbox['height']) / 100 * page_height
    #print("darw bbox: ", x, y, width, height)
    # Draw the rectangle
    can.rect(x, y, width, height)
    # print("drawing", x, y + height, width, height, color)

    # Draw the label for element type in the top left corner
    type_label = f"{element['type']}"
    can.setFont("Helvetica", 6)
    type_label_width = can.stringWidth(type_label) + 2
    type_label_height = 4
    can.setFillColor(color)  # Set fill color to the same as the rect color
    can.rect(x, y + height - type_label_height - 2, type_label_width+2, type_label_height+2, fill=1)  # Draw filled rectangle
    textcolor = 'white' if color not in ['#FFFF99', '#FFFF66'] else 'black'

    can.setFillColor(textcolor)  # Set text color to white
    can.drawString(x+2, y + height - type_label_height -1, type_label)

    """# Draw the label for x, y, w, h in the bottom right corner (inside)
    relative_x = round(float(bbox['x']), 2)
    relative_y = round(float(bbox['y']), 2)
    relative_width = round(float(bbox['width']), 2)
    relative_height = round(float(bbox['height']), 2)
    xywh_label = f"x:{relative_x}% y:{relative_y}% w:{relative_width}% h:{relative_height}%"
    can.setFillColor('black')
    can.setFont("Helvetica", 3)
    xywh_label_width = can.stringWidth(xywh_label) + 2
    xywh_label_height = 4
    can.setStrokeColor('black')
    can.rect(x + width - xywh_label_width, y, xywh_label_width, xywh_label_height, fill=1)
    can.setFillColor('white')
    can.drawString(x + width - xywh_label_width + 1, y + 1, xywh_label)
    
    # Draw the label for x, y, w, h in the bottom right corner (inside)
    xywh_label = f"x:{x:.2f} y:{y:.2f} w:{width:.2f} h:{height:.2f}"
    can.setFillColor('black')
    can.setFont("Helvetica", 3)
    xywh_label_width = can.stringWidth(xywh_label) + 2
    xywh_label_height = 4
    can.setStrokeColor('black')
    can.rect(x + width - xywh_label_width, y, xywh_label_width, xywh_label_height, fill=1)
    can.setFillColor('white')
    can.drawString(x + width - xywh_label_width + 1, y + 1, xywh_label)"""

def process_elements(elements, can, page_num, colors, dpi, margin, page_height):
    for element in elements:
        if isinstance(element, dict):  # Ensure element is a dictionary
            # Check if the element is on the current page
            if element.get('page_number') == page_num + 1:  # Page numbers are 1-based
                if 'bounding_box' in element:
                    bbox = element['bounding_box']
                    # print(f"Drawing bbox on page {page_num + 1}: {bbox}")  # Debugging: Log bounding box details
                    color = colors.get(element.get("type", "unknown"), 'black')
                    # Draw the bounding box
                    draw_bbox(can, bbox, color, dpi, margin, page_height, element)
            # Recursively process nested content
            if 'content' in element:
                process_elements(element['content'], can, page_num, colors, dpi, margin, page_height)

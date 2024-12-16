from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
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

class PDFGeneratorHTMLCSS(PDFGeneratorBase):
    def generate_pdf(self):
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PDF Content</title>
            <style>
                @page {{
                    size: 8.27in 11.69in;  /* A4 size in inches */
                    margin: 0;  /* No margin */
                }}
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;  /* Remove margin from body */
                    padding: 0;  /* No padding */
                    width: 8.27in;  /* Full width of A4 */
                    height: 11.69in;  /* Full height of A4 */
                    background-color: lightgray;  /* Added background color */
                    box-sizing: border-box;  /* Include border in the element's total width and height */
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }}
                .page {{
                    width: 7.87in;  /* A4 width minus 1cm padding on each side */
                    height: 10.69in;  /* A4 height minus 1cm padding on top and bottom */
                    margin: 0.39in;  /* 1cm margin */
                    background-color: white;
                    box-shadow: 0 0 0.5cm rgba(0,0,0,0.5);
                    box-sizing: border-box;
                    padding: 1cm;
                    overflow: hidden;
                    page-break-after: always;
                }}
                h1, h2, p, ul {{
                    margin: 0;
                    padding: 0;
                }}
                h1 {{
                    font-size: 24px;
                    margin-bottom: 0.5em;
                }}
                h2 {{
                    font-size: 20px;
                    margin-bottom: 0.5em;
                }}
                p {{
                    font-size: 16px;
                    margin-bottom: 1em;
                }}
                ul {{
                    list-style-type: disc;
                    margin-left: 20px;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                }}
                @media print {{
                    body {{
                        margin: 0;  /* Ensure print media has no margin */
                        padding: 0;  /* Ensure print media has no padding */
                        width: 8.27in;  /* Full width of A4 */
                        height: 11.69in;  /* Full height of A4 */
                    }}
                    .page {{
                        margin: 0;  /* No margin for print */
                        box-shadow: none;  /* Remove shadow for print */
                        page-break-after: always;
                    }}
                }}
                .bbox {{
                    position: absolute;
                    border: 2px solid;
                }}
                .bbox span {{
                    background-color: black;
                    color: white;
                    padding: 2px;
                }}
            </style>
            <!-- ADDITIONAL CSS -->
        </head>
        <body>
        <div class="page">
        """
        element_ids = {}  # Dictionary to store element IDs

        for section in self.data.get('content', []):
            if section['type'] == 'heading':
                for element in section['content']:
                    element_id = str(uuid.uuid4())
                    if element['type'] == 'title':
                        html_content += f"<h1 id='{element_id}'>{element['content']}</h1>"
                        element_ids[element_id] = element
                    elif element['type'] == 'subtitle':
                        html_content += f"<h2 id='{element_id}'>{element['content']}</h2>"
                        element_ids[element_id] = element
            elif section['type'] == 'section':
                for element in section.get('content', []):
                    element_id = str(uuid.uuid4())
                    if element['type'] == 'title':
                        html_content += f"<h2 id='{element_id}'>{element['content']}</h2>"
                        element_ids[element_id] = element
                    elif element['type'] == 'text':
                        html_content += f"<p id='{element_id}'>{element['content']}</p>"
                        element_ids[element_id] = element
                    elif element['type'] == 'list':
                        html_content += f"<ul id='{element_id}'>"
                        element_ids[element_id] = element  # Store the entire list element
                        # Convert list items to dictionaries
                        for i, item in enumerate(element['content']):
                            if isinstance(item, str):
                                element['content'][i] = {'content': item}
                        for item in element['content']:
                            item_id = str(uuid.uuid4())
                            html_content += f"<li id='{item_id}'>{item['content']}</li>"
                            element_ids[item_id] = item
                        html_content += "</ul>"
                        element_ids[element_id] = element
                    elif element['type'] == 'image':
                        html_content += f"<img id='{element_id}' src='images/{element['content']}' alt='Image' />"
                        element_ids[element_id] = element

        html_content += "</div><!-- ADDITIONAL HTML--></body></html>"
        # Save HTML content to a temporary file
        temp_html_path = os.path.abspath(self.output_path.replace('.pdf', '.html'))
        os.makedirs(os.path.dirname(temp_html_path), exist_ok=True)
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"HTML content saved to {temp_html_path}")

        # Start a simple HTTP server to serve the HTML file
        PORT = 8000
        Handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(("", PORT), Handler)

        def start_server():
            os.chdir(os.path.dirname(temp_html_path))  # Change directory to where the HTML file is located
            httpd.serve_forever()

        server_thread = threading.Thread(target=start_server)
        server_thread.daemon = True
        server_thread.start()

        print("Creating ChromeDriver instance")

        chrome_options = Options()  # Create an instance of Options
        #chrome_options.add_argument("--headless")  # Run in headless mode
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
        try:
            # Force redownload by setting cache_valid_range in the install method
            driver_path = ChromeDriverManager().install()
            driver = webdriver.Chrome(service=Service(driver_path), options=chrome_options)
            print("ChromeDriver instance created successfully")
        except Exception as e:
            print(f"Failed to create ChromeDriver instance: {e}")
            raise

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
            driver.get(f'file://{temp_html_path}')
            time.sleep(2)  # Wait for the page to load

            # Emulate print media
            driver.execute_script('document.body.style.zoom="100%"')
            driver.execute_cdp_cmd('Emulation.setEmulatedMedia', {'media': 'print'})

            # Extract positions and bounding boxes
            wait = WebDriverWait(driver, 20)  # Increase timeout to 20 seconds
            for element_id, element in element_ids.items():
                print(f"Looking for element with ID: {element_id}")
                web_element = wait.until(EC.presence_of_element_located((By.ID, element_id)))
                bounding_box = driver.execute_script("""
                    var rect = arguments[0].getBoundingClientRect();
                    return {x: rect.left, y: rect.top, width: rect.width, height: rect.height};
                """, web_element)
                page_number = 1  # Assuming single-page PDF for simplicity

                # Update the element with bounding box and page number
                element['bounding_box'] = bounding_box
                element['page_number'] = page_number

            # Create bounding box divs
            bbox_divs = ""
            colors = {
                'title': 'red',
                'subtitle': 'blue',
                'text': 'green',
                'list': 'purple',
                'image': 'orange'
            }

            for element_id, element in element_ids.items():
                bbox = element['bounding_box']
                element_type = element.get('type', 'unknown')
                color = colors.get(element_type, 'black')
                label = element_type

                bbox_divs += f"""
                <div class="bbox" style="top:{bbox['y']}px; left:{bbox['x']}px; width:{bbox['width']}px; height:{bbox['height']}px; border-color:{color};">
                    <span style="background-color:{color};">{label}</span>
                </div>
                """

            # Inject bounding box divs into the DOM
            driver.execute_script(f"""
                var bboxContainer = document.createElement('div');
                bboxContainer.innerHTML = `{bbox_divs}`;
                document.body.appendChild(bboxContainer);
            """)

            # Print to PDF
            result = driver.execute_cdp_cmd("Page.printToPDF", print_options)
            output_dir = os.path.dirname(self.output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            with open(self.output_path, 'wb') as pdf_file:
                pdf_file.write(base64.b64decode(result['data']))

        finally:
            httpd.shutdown()
            driver.quit()

        with open(self.output_path.replace('.pdf', '.pdf.json'), 'w') as json_file:
            json.dump(self.data, json_file, indent=4)

        # Validate bounding boxes and draw them on the PDF
        def draw_bounding_boxes(input_pdf_path, output_pdf_path, element_ids):
            input_pdf = PdfReader(open(input_pdf_path, "rb"))
            output_pdf = PdfWriter()

            margin = 0  # No margin
            dpi = 96  # Set both screen and PDF DPI to 96

            for page_num in range(len(input_pdf.pages)):
                page = input_pdf.pages[page_num]
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=A4)

                for element_id, element in element_ids.items():
                    if element['page_number'] == page_num + 1:  # Page numbers are 1-based
                        bbox = element['bounding_box']
                        color = colors.get(element.get('type', 'unknown'), 'black')
                        can.setStrokeColor(color)
                        can.setLineWidth(2)
                        # Adjust bounding box coordinates by considering the margins and DPI
                        x = bbox['x'] * (72 / dpi) + margin
                        y = A4[1] - (bbox['y'] * (72 / dpi) + margin + bbox['height'] * (72 / dpi))
                        width = bbox['width'] * (72 / dpi)
                        height = bbox['height'] * (72 / dpi)
                        can.rect(x, y, width, height)
                        print(f"Drawing bbox for element {element_id}: x={x}, y={y}, width={width}, height={height}")

                can.save()
                packet.seek(0)
                new_pdf = PdfReader(packet)

                if len(new_pdf.pages) > 0:  # Ensure new_pdf contains pages
                    page.merge_page(new_pdf.pages[0])
                output_pdf.add_page(page)

            with open(output_pdf_path, "wb") as outputStream:
                output_pdf.write(outputStream)

        draw_bounding_boxes(self.output_path, self.output_path.replace('.pdf', '_bbox.pdf'), element_ids)

# TODO:
# - we can add all elements one item at a time with javascript in the browser, and then we can detect if it shall be put on the next page or not.

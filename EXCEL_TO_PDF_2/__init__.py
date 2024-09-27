from flask import Flask, render_template, request, send_file, abort, url_for, redirect, jsonify, Blueprint
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image as ReportLabImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
import os
import logging
from openpyxl import load_workbook
from PIL import Image as PILImage
from bs4 import BeautifulSoup
import werkzeug
import re
import uuid
from __main__ import db, app
import logging


project2 = Blueprint("case2", __name__, template_folder='templates', static_folder='static')
logging.basicConfig(level=logging.DEBUG)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = os.path.join('EXCEL_TO_PDF_2/static', UPLOAD_FOLDER)

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def extract_images_from_excel(file_path):
    wb = load_workbook(file_path)
    ws = wb.active
    images = {}
    ensure_directory_exists('static/images')
    
    for i, image in enumerate(ws._images, start=1):
        img_filename = f"static/images/{i}.png"
        img_data = image.ref
        if isinstance(img_data, BytesIO):
            img_data = img_data.getvalue()
        pil_image = PILImage.open(BytesIO(img_data))
        pil_image.save(img_filename)
        images[i] = i
    
    return images

def process_excel_file(file_path):
    try:
        images = extract_images_from_excel(file_path)
        df = pd.read_excel(file_path, engine='openpyxl', header=1, dtype={'No.': str})
        
        desired_columns = ['No.', 'Unique Model Code', "Product's Name", 'Photo', 'Specification', 'Additional Info', 'Price']
        
        df.columns = [desired_columns[i] if i < len(desired_columns) else f'Column_{i}' for i in range(len(df.columns))]
        
        for col in desired_columns:
            if col not in df.columns:
                df[col] = ''
        
        df = df[desired_columns]
        df = df.fillna('')
        
        # Convert 'No.' to numeric if possible, otherwise keep as string
        df['No.'] = pd.to_numeric(df['No.'], errors='coerce').fillna(df['No.'])
        
        # Convert 'Price' to numeric, removing any currency symbols and handling 'USD'
        def clean_price(price):
            if isinstance(price, str):
                price = re.sub(r'[^\d.]', '', price)
            try:
                return float(price)
            except ValueError:
                return 0.0  # or another default value

        df['Price'] = df['Price'].apply(clean_price)
        
        return df, images
    except Exception as e:
        app.logger.error(f"Error processing Excel file: {str(e)}")
        return None, None

def generate_html_table(df, images):
    html = '<table border="1" class="dataframe data table table-striped" style="width:100%; max-width:1000px; margin: auto;">\n'
    html += '  <thead>\n    <tr style="text-align: center;">\n'
    for col in df.columns:
        html += f'      <th contenteditable="true">{col}</th>\n'
    html += '    </tr>\n  </thead>\n  <tbody>\n'
    
    for i, row in df.iterrows():
        html += '    <tr>\n'
        for j, value in enumerate(row):
            cell_content = str(value)
            if df.columns[j] == 'Photo':
                try:
                    item_number = int(float(row['No.'])) if row['No.'] and not pd.isna(row['No.']) else None
                except ValueError:
                    item_number = None
                
                if item_number is not None and item_number in images:
                    img_url = url_for('case2.static', filename=f'images/{images[item_number]}.png')
                    cell_content = f'<img src="{img_url}" alt="Product Image" width="100" height="100">'
                else:
                    cell_content = f"No image (Item: {item_number})"
            elif df.columns[j] == 'Price':
                try:
                    numeric_value = float(value)
                    cell_content = f"{numeric_value:.2f}"
                except ValueError:
                    cell_content = value
            
            html += f'      <td contenteditable="true">{cell_content}</td>\n'
        html += '    </tr>\n'
    
    html += '  </tbody>\n</table>'
    return html

@project2.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = werkzeug.utils.secure_filename(file.filename)
            ensure_directory_exists(app.config['UPLOAD_FOLDER'])
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            return redirect(url_for('case2.view_file', filename=filename))
    return render_template('EXCEL_TO_PDF_2/index.html')

@project2.route('/view/<filename>')
def view_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df, images = process_excel_file(file_path)
    if df is None:
        abort(500, description="Error processing Excel file")
    
    html_table = generate_html_table(df, images)
    return render_template('EXCEL_TO_PDF_2/view.html', table=html_table, filename=filename)

@project2.route('/upload_image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return jsonify({'image_url': url_for('case2.static', filename=f'{UPLOAD_FOLDER}/{filename}')}), 200
    return jsonify({'error': 'File type not allowed'}), 400

@project2.route('/download_pdf', methods=['POST'])
def download_pdf():
    logging.info("Entering download_pdf function")
    
    table_html = request.form.get('table_data')
    if not table_html:
        logging.error("No table data received")
        return "No table data received", 400
    
    logging.info(f"Received table HTML: {table_html[:500]}...")  # Log first 500 characters
    
    soup = BeautifulSoup(table_html, 'html.parser')
    tables = soup.find_all('table')
    
    if not tables:
        logging.error("No tables found in the submitted data")
        return "No tables found in the submitted data", 400
    
    logging.info(f"Number of tables found: {len(tables)}")
    
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle('Normal', fontSize=8, leading=10, alignment=TA_CENTER)
    header_style = ParagraphStyle('Header', fontSize=10, leading=12, alignment=TA_CENTER, fontName='Helvetica-Bold')
    
    pdf_data = []
    
    for table_index, table in enumerate(tables):
        logging.info(f"Processing table {table_index + 1}")
        
        # Process the header
        header_row = []
        thead = table.find('thead')
        if thead:
            ths = thead.find_all('th')
            for th in ths:
                header_text = th.text.strip()
                header_row.append(Paragraph(header_text, header_style))
        
        if header_row and not pdf_data:  # Only add header once
            pdf_data.append(header_row)
            logging.info("Header row added to pdf_data")
        
        # Process the body
        rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')[1:]
        logging.info(f"Number of rows in table {table_index + 1}: {len(rows)}")
        
        for row_index, tr in enumerate(rows):
            row_data = []
            tds = tr.find_all('td')
            for td in tds:
                if td.find('img'):
                    # Image processing code...
                    logging.info(f"Image found in table {table_index + 1}, row {row_index + 1}")
                else:
                    cell_content = td.text.strip()
                    row_data.append(Paragraph(cell_content, normal_style))
            pdf_data.append(row_data)
        
        logging.info(f"Finished processing table {table_index + 1}")
    
    logging.info(f"Total number of rows in pdf_data: {len(pdf_data)}")
    
    if pdf_data:
        # Table creation code...
        logging.info("Creating PDF table")
        
        # ... (rest of the table creation code)
        
        elements = [pdf_table]
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
        
        logging.info("Attempting to build PDF document")
        try:
            doc.build(elements)
            logging.info("PDF document built successfully")
        except LayoutError:
            logging.warning("Table too large, attempting to reduce size")
            # ... (size reduction code)
            doc.build(elements)
            logging.info("PDF document built successfully after size reduction")
        
        buffer.seek(0)
        
        logging.info("Returning PDF file")
        return send_file(buffer, as_attachment=True, download_name='table_data.pdf', mimetype='application/pdf')
    else:
        logging.error("No data to generate PDF")
        return "No data to generate PDF", 400
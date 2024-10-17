from flask import Blueprint, render_template, request, send_file, abort, url_for, redirect, jsonify, current_app, send_from_directory
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
# from Quresh_Database.database import db

project2 = Blueprint('excel_to_pdf', __name__,
                     template_folder='templates',
                     static_folder='static',
                     static_url_path='/excel_to_pdf/static')

logging.basicConfig(level=logging.DEBUG)

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'png', 'jpg', 'jpeg', 'gif'}

# def init_app(app):
#     app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
#     app.config['EXCEL_TO_PDF_UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
#     os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def extract_images_from_excel(file_path):
    wb = load_workbook(file_path)
    ws = wb.active
    images = {}
    
    for i, image in enumerate(ws._images, start=1):
        img_filename = f"{i}.png"
        img_path = os.path.join(current_app.config['EXCEL_TO_PDF_UPLOAD_FOLDER'], img_filename)
        img_data = image.ref
        if isinstance(img_data, BytesIO):
            img_data = img_data.getvalue()
        pil_image = PILImage.open(BytesIO(img_data))
        pil_image.save(img_path)
        images[i] = img_filename
        current_app.logger.debug(f"Saved image: {img_path}")
    
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
        current_app.logger.error(f"Error processing Excel file: {str(e)}")
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
                    img_filename = images[item_number]
                    img_url = url_for('static', filename=f'uploads/{img_filename}')
                    current_app.logger.debug(f"Item {item_number}: Generated image URL: {img_url}")
                    cell_content = f'<img src="{img_url}" alt="Product Image" width="100" height="100">'
                else:
                    current_app.logger.warning(f"No image found for item number: {item_number}")
                    cell_content = f"No image (Item: {item_number})"
            elif df.columns[j] == 'Price':
                try:
                    numeric_value = float(value)
                    cell_content = f"{numeric_value:.2f}"
                except ValueError:
                    current_app.logger.warning(f"Invalid price value: {value}")
                    cell_content = value
            
            html += f'      <td contenteditable="true">{cell_content}</td>\n'
        html += '    </tr>\n'
    
    html += '  </tbody>\n</table>'
    return html





@project2.route('/', methods=['GET', 'POST'])
def index():
    print("Excel to PDF index route hit!")
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = werkzeug.utils.secure_filename(file.filename)
            ensure_directory_exists(current_app.config['UPLOAD_FOLDER'])
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            return redirect(url_for('excel_to_pdf.view_file', filename=filename))
    return render_template('index.html')

@project2.route('/uploads/<path:filename>')
def serve_image(filename):
    return send_from_directory(current_app.config['EXCEL_TO_PDF_UPLOAD_FOLDER'], filename)


@project2.route('/view/<filename>')
def view_file(filename):
    file_path = os.path.join(current_app.config['EXCEL_TO_PDF_UPLOAD_FOLDER'], filename)
    df, images = process_excel_file(file_path)
    if df is None:
        abort(500, description="Error processing Excel file")
    
    html_table = generate_html_table(df, images)
    return render_template('view.html', table=html_table, filename=filename)

@project2.route('/upload_image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return jsonify({'image_url': url_for('static', filename=f'uploads/{filename}')}), 200
    return jsonify({'error': 'File type not allowed'}), 400

@project2.route('/download_pdf', methods=['POST'])
def download_pdf():
    current_app.logger.info("PDF download request received")
    table_html = request.form.get('table_data')
    if not table_html:
        current_app.logger.error("No table data received")
        return "No table data received", 400
    
    current_app.logger.info(f"Received table HTML: {table_html[:500]}...")  # Log first 500 characters
    
    soup = BeautifulSoup(table_html, 'html.parser')
    tables = soup.find_all('table')
    
    if not tables:
        current_app.logger.error("No tables found in the submitted data")
        return "No tables found in the submitted data", 400
    
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle('Normal', fontSize=8, leading=10, alignment=TA_CENTER)
    header_style = ParagraphStyle('Header', fontSize=10, leading=12, alignment=TA_CENTER, fontName='Helvetica-Bold')
    
    elements = []
    
    for table_index, table in enumerate(tables):
        pdf_data = []
        
        # Process the header
        header_row = []
        thead = table.find('thead')
        if thead:
            ths = thead.find_all('th')
            for i, th in enumerate(ths):
                if i == 0 or i == len(ths) - 1:
                    header_text = th.text.strip()
                    header_row.append(Paragraph(header_text, header_style))
                else:
                    header_row.append(Paragraph("", header_style))
        
        if header_row:
            pdf_data.append(header_row)
        
        # Process the body
        rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')[1:]
        
        for tr in rows:
            row_data = []
            tds = tr.find_all('td')
            for i, td in enumerate(tds):
                if i == len(tds) - 1:  # Price column (last column)
                    cell_content = td.text.strip()
                    row_data.append(Paragraph(cell_content, normal_style))
                elif td.find('img'):  # Image column
                    img = td.find('img')
                    img_src = img.get('src')
                    if img_src:
                        img_filename = os.path.basename(img_src)
                        img_path = os.path.join(current_app.root_path, 'static', 'uploads', img_filename)
                        if os.path.exists(img_path):
                            try:
                                img = ReportLabImage(img_path, width=1.5*inch, height=1.5*inch)
                                row_data.append(img)
                            except Exception as e:
                                current_app.logger.error(f"Error loading image {img_path}: {str(e)}")
                                row_data.append(Paragraph(f"Error loading image", normal_style))
                        else:
                            current_app.logger.error(f"Image not found: {img_path}")
                            row_data.append(Paragraph("Image not found", normal_style))
                    else:
                        row_data.append(Paragraph("No image source", normal_style))
                else:
                    cell_content = td.text.strip()
                    row_data.append(Paragraph(cell_content, normal_style))
            pdf_data.append(row_data)
        
        if len(pdf_data) > 0:
            # Adjust column widths
            page_width, page_height = landscape(A4)
            available_width = page_width - 40  # Subtracting left and right margins
            first_last_column_width = 0.8 * inch
            remaining_width = available_width - (2 * first_last_column_width)
            middle_column_width = remaining_width / (len(pdf_data[0]) - 2)  # Subtract 2 for first and last columns
            
            col_widths = [first_last_column_width] + [middle_column_width] * (len(pdf_data[0]) - 2) + [first_last_column_width]
            
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ])
            
            pdf_table = Table(pdf_data, repeatRows=1, colWidths=col_widths)
            pdf_table.setStyle(table_style)
            elements.append(pdf_table)
    
    if elements:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
        
        # Try to build the document, if it fails due to LayoutError, reduce the table size
        try:
            doc.build(elements)
        except LayoutError:
            current_app.logger.warning("Table too large, attempting to reduce size")
            for element in elements:
                if isinstance(element, Table):
                    element._argW = [0.95*w for w in element._argW]  # Reduce width by 5%
                    for i, row in enumerate(element._cellvalues):
                        for j, cell in enumerate(row):
                            if isinstance(cell, Paragraph):
                                element._cellvalues[i][j] = Paragraph(cell.text, ParagraphStyle('Reduced', fontSize=7, leading=8, alignment=TA_CENTER))
                            elif isinstance(cell, ReportLabImage):
                                cell.drawWidth *= 0.95
                                cell.drawHeight *= 0.95
            doc.build(elements)
        
        buffer.seek(0)
        
        current_app.logger.info("PDF generated successfully")
        return send_file(buffer, as_attachment=True, download_name='table_data.pdf', mimetype='application/pdf')
    else:
        current_app.logger.error("No data to generate PDF")
        return "No data to generate PDF", 400
    
    @project2.route('/test')
    def test():
        return "Excel to PDF blueprint is working!"
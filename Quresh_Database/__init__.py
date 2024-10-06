from flask import Blueprint, render_template, request, send_file, redirect, url_for, flash, jsonify, current_app
from werkzeug.utils import secure_filename
import pandas as pd
from io import BytesIO
import os
from openpyxl import load_workbook
from openpyxl_image_loader import SheetImageLoader
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image as ReportLabImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import base64
from sqlalchemy.exc import IntegrityError
import logging
from sqlalchemy.sql import func
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch
from io import BytesIO
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter, landscape
from flask import render_template, request, Blueprint, url_for, flash, redirect, send_file

# Import db from the database module
from database import db

project1 = Blueprint('excel_to_db', __name__, template_folder='templates', static_folder='static')

@project1.app_template_filter('b64encode')
def b64encode_filter(data):
    if data is None:
        return ''
    return base64.b64encode(data).decode('utf-8')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    no = db.Column(db.Integer, unique=True, nullable=False)
    unique_model_code = db.Column(db.String(50), unique=True, nullable=False)
    image = db.Column(db.LargeBinary)
    product_name = db.Column(db.String(100), nullable=False)
    specification = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __init__(self, **kwargs):
        super(Product, self).__init__(**kwargs)
        if not self.no:
            last_product = Product.query.order_by(Product.no.desc()).first()
            self.no = (last_product.no + 1) if last_product else 1

# ... rest of the file remains the same ...

@project1.route('/', methods=['GET'])
def index():
    search_query = request.args.get('search', '').strip()
    if search_query:
        products = Product.query.filter(
            db.or_(
                Product.product_name.ilike(f'%{search_query}%'),
                Product.unique_model_code.ilike(f'%{search_query}%'),
                Product.specification.ilike(f'%{search_query}%')
            )
        ).all()
    else:
        products = Product.query.all()
    return render_template('Quresh_Database/index.html', products=products, search_query=search_query)

@project1.app_template_filter('highlight')
def highlight_filter(text, search_term):
    if not search_term:
        return text
    highlighted = text.replace(search_term, f'<span class="highlight">{search_term}</span>')
    return highlighted


@project1.route('/upload_excel', methods=['GET', 'POST'])
def upload_excel():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and file.filename.endswith('.xlsx'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            try:
                processed_rows, skipped_rows = process_excel(file_path)
                flash(f'Excel file processed successfully. Processed {processed_rows} rows, skipped {skipped_rows} rows.', 'success')
            except Exception as e:
                flash(f'Error processing Excel file: {str(e)}', 'error')
            finally:
                os.remove(file_path)
            return redirect(url_for('excel_to_db.index'))
    return render_template('Quresh_Database/upload_excel.html')



@project1.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    print("This is the correct generate_pdf function")
    product_ids = request.json.get('product_ids', [])
    products = Product.query.filter(Product.id.in_(product_ids)).all()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    
    # Define column widths as percentages of the page width
    page_width = landscape(letter)[0] - 40  # Subtracting left and right margins
    col_widths = [
        0.15 * page_width,  # Product
        0.08 * page_width,  # No.
        0.15 * page_width,  # Unique Model Code
        0.27 * page_width,  # Specification
        0.10 * page_width,  # Price
        0.25 * page_width,  # Image
    ]
    
    # Create table data
    table_data = [["Product", "No.", "Unique Model Code", "Specification", "Price", "Image"]]  # Header row
    
    for product in products:
        row = [
            Paragraph(product.product_name, styles['Normal']),
            str(product.no),
            Paragraph(product.unique_model_code, styles['Normal']),
            Paragraph(product.specification, styles['Normal']),
            f"${product.price:.2f}",
            ""  # Placeholder for image
        ]
        if product.image:
            img_buffer = BytesIO(product.image)
            img = PILImage.open(img_buffer)
            img_width, img_height = img.size
            aspect = img_height / float(img_width)
            
            max_width = col_widths[-1]  # Use the width of the image column
            img_width = min(img_width, max_width)
            img_height = img_width * aspect
            
            temp_img = BytesIO()
            img.save(temp_img, format='PNG')
            temp_img.seek(0)
            
            img = ReportLabImage(temp_img, width=img_width, height=img_height)
            row[-1] = img  # Replace placeholder with actual image
        
        table_data.append(row)
    
    # Create table
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
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
        ('WORDWRAP', (0, 0), (-1, -1)),  # Enable word wrapping for all cells
    ]))
    
    # Build PDF
    elements = [table]
    doc.build(elements)
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='selected_products.pdf', mimetype='application/pdf')


@project1.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        try:
            new_product = Product(
                unique_model_code=request.form.get('unique_model_code'),
                product_name=request.form.get('product_name'),
                specification=request.form.get('specification'),
                price=float(request.form.get('price', 0)),
            )
            if 'image' in request.files:
                file = request.files['image']
                if file.filename != '':
                    new_product.image = file.read()
            
            db.session.add(new_product)
            db.session.commit()
            flash('Product added successfully')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while adding the product. The unique model code may already be in use.')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {str(e)}')
        return redirect(url_for('excel_to_db.index'))
    return render_template('Quresh_Database/add_product.html')

@project1.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        try:
            product.unique_model_code = request.form.get('unique_model_code')
            product.product_name = request.form.get('product_name')
            product.specification = request.form.get('specification')
            product.price = float(request.form.get('price', 0))
            if 'image' in request.files:
                file = request.files['image']
                if file.filename != '':
                    product.image = file.read()
            
            db.session.commit()
            flash('Product updated successfully')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while updating the product. The unique model code may already be in use.')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {str(e)}')
        return redirect(url_for('excel_to_db.index'))
    return render_template('Quresh_Database/edit_product.html', product=product)

@project1.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully')
    return redirect(url_for('excel_to_db.index'))

@project1.route('/update_image/<int:product_id>', methods=['POST'])
def update_image(product_id):
    product = Product.query.get_or_404(product_id)
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            product.image = file.read()
            db.session.commit()
            flash('Image updated successfully')
    return redirect(url_for('excel_to_db.index'))

def process_excel(file_path):
    with current_app.app_context():
        try:
            # Skip the first 2 rows (headers) and use the 3rd row as column names
            df = pd.read_excel(file_path, skiprows=2, header=0)

            df = df.rename(columns={
                'Unnamed: 1': 'unique_model_code',
                'Unnamed: 2': 'product_name',
                'Unnamed: 4': 'specification',
                'USD': 'price'
            })

            workbook = load_workbook(file_path)
            sheet = workbook.active
            image_loader = SheetImageLoader(sheet)
            skipped_rows = 0
            processed_rows = 0

            for i, (_, row) in enumerate(df.iterrows(), start=4):
                try:
                    if not _is_valid_row(row):
                        current_app.logger.warning(f"Skipping row with invalid unique_model_code: {row}")
                        skipped_rows += 1
                        continue

                    image = _get_image(image_loader, i)
                    file = _prepare_image_file(image) if image else None

                    product = _create_product(row, file)
                    db.session.add(product)
                    db.session.flush()
                    processed_rows += 1

                except IntegrityError:
                    db.session.rollback()
                    current_app.logger.warning(f"Skipping row with duplicate unique_model_code: {row['unique_model_code']}")
                    skipped_rows += 1
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error processing row: {row}", exc_info=True)
                    skipped_rows += 1

            db.session.commit()
            return processed_rows, skipped_rows

        except Exception as e:
            db.session.rollback()
            current_app.logger.error("Error processing Excel file", exc_info=True)
            raise

def _is_valid_row(row):
    return not pd.isna(row['unique_model_code']) and str(row['unique_model_code']).strip() != ''

def _get_image(image_loader, row_number):
    try:
        return image_loader.get(f"D{row_number}")
    except:
        current_app.logger.warning(f"No image found for row {row_number}, skipping image")
        return None

def _prepare_image_file(image):
    path = f"./static/temp_image.{image.format}"
    image.save(path)
    with open(path, "rb") as x:
        file = x.read()
    os.remove(path)  # Clean up the temporary file
    return file

def _create_product(row, image_file):
    return Product(
        unique_model_code=str(row['unique_model_code']),
        product_name=str(row['product_name']),
        image=image_file,
        specification=str(row['specification']),
        price=float(row['price']) if pd.notnull(row['price']) else 0.0,
    )
import os
from flask import Flask, render_template, request, send_file, redirect, url_for, flash, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import pandas as pd
from PIL import Image
from io import BytesIO
import os
from openpyxl import load_workbook
from openpyxl_image_loader import SheetImageLoader
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import base64
from sqlalchemy.exc import IntegrityError
import logging
import pandas as pd
from __main__ import app, db
from sqlalchemy.sql import func

project1 = Blueprint('excel_to_db', __name__, template_folder='templates', static_folder='static')

@app.template_filter('b64encode')
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

@project1.route('/')
def index():
    products = Product.query.all()
    return render_template('Quresh_Database/index.html', products=products)

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
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            process_excel(file_path)
            os.remove(file_path)  # Remove the file after processing
            flash('Excel file processed successfully')
            return redirect(url_for('excel_to_db.index'))
    return render_template('Quresh_Database/upload_excel.html')

@project1.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    product_ids = request.json.get('product_ids', [])
    products = Product.query.filter(Product.id.in_(product_ids)).all()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    for product in products:
        elements.append(Paragraph(f"Product: {product.product_name}", styles['Heading2']))
        data = [
            ["No.", str(product.no)],
            ["Unique Model Code", product.unique_model_code],
            ["Specification", product.specification],
            ["Price", f"${product.price:.2f}"],
        ]
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (1, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (1, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 0),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)

        if product.image:
            img = Image(BytesIO(product.image))
            img.drawHeight = 200
            img.drawWidth = 200
            elements.append(img)

        elements.append(PageBreak())

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
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

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
        i = 4  # Starting row for images

        for _, row in df.iterrows():
            try:
                # Check if unique_model_code is present and valid
                if pd.isna(row['unique_model_code']) or str(row['unique_model_code']).strip() == '':
                    logger.warning(f"Skipping row with invalid unique_model_code: {row}")
                    skipped_rows += 1
                    i += 1
                    continue

                # Try to get the image
                try:
                    image = image_loader.get(f"D{i}")
                except:
                    logger.warning(f"No image found for row {i}, skipping image")
                    image = None

                i += 1

                # Prepare the image file if it exists
                file = None
                if image:
                    path = f"./static/temp_image.{image.format}"
                    image.save(path)
                    with open(path, "rb") as x:
                        file = x.read()
                    os.remove(path)  # Clean up the temporary file

                # Create the product
                product = Product(
                    unique_model_code=str(row['unique_model_code']),
                    product_name=str(row['product_name']),
                    image=file,
                    specification=str(row['specification']),
                    price=float(row['price']) if pd.notnull(row['price']) else 0.0,
                )

                db.session.add(product)
                try:
                    db.session.flush()
                    processed_rows += 1
                except IntegrityError:
                    db.session.rollback()
                    skipped_rows += 1
                    logger.warning(f"Skipping row with duplicate unique_model_code: {row['unique_model_code']}")
                    continue
                except Exception as e:
                    db.session.rollback()
                    skipped_rows += 1
                    logger.error(f"Error processing row: {row}")
                    logger.error(f"Error details: {str(e)}")
                    continue

            except Exception as e:
                logger.error(f"Error processing row: {row}")
                logger.error(f"Error details: {str(e)}")
                skipped_rows += 1
                continue

        db.session.commit()
        flash(f'Excel file processed successfully. Processed {processed_rows} rows, skipped {skipped_rows} rows.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing Excel file: {str(e)}")
        flash(f'Error processing Excel file: {str(e)}', 'error')
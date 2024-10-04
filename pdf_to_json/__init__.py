from flask import Blueprint, render_template, request, send_file
from werkzeug.utils import secure_filename
import os
from io import BytesIO
from .extract_text_table_info_with_figures_tables_renditions import ExtractTextTableInfoWithFiguresTablesRenditionsFromPDF

pdf_to_json = Blueprint('pdf_to_json', __name__, template_folder='../templates')

@pdf_to_json.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'PDF' not in request.files:
            return 'No file part'
        file = request.files['PDF']
        if file.filename == '':
            return 'No selected file'
        if file:
            filename = secure_filename(file.filename)
            try:
                extractor = ExtractTextTableInfoWithFiguresTablesRenditionsFromPDF(file)
                result = extractor.get_result()
                return send_file(
                    BytesIO(result),
                    download_name=f'extracted_{filename}.zip',
                    as_attachment=True
                )
            except Exception as e:
                return str(e)

    return render_template('pdf_to_json/index.html')

# This line ensures that the 'project3' name is exported
project3 = pdf_to_json
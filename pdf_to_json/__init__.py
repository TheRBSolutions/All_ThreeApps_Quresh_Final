from flask import Blueprint, render_template, request, flash, redirect,send_file, url_for
from pdf_to_json.extract_text import ExtractTextInfoFromPDF
from pdf_to_json.extract_text_table_info import ExtractTextTableInfoFromPDF
from pdf_to_json.extract_text_table_info_with_char_bounds import ExtractTextTableInfoWithCharBoundsFromPDF
from pdf_to_json.extract_text_table_info_with_styling import ExtractTextTableInfoWithStylingFromPDF
from pdf_to_json.extract_text_table_info_with_figures_tables_renditions import ExtractTextTableInfoWithFiguresTablesRenditionsFromPDF
from pdf_to_json.text_info_with_char_bounds import ExtractTextInfoWithCharBoundsFromPDF
from pdf_to_json.extract_text_table_info_with_table_structure import ExtractTextTableInfoWithTableStructureFromPDF
from io import BytesIO

project3 = Blueprint('pdf_to_json', __name__, template_folder='templates')

@project3.route('/', methods=["POST", "GET"])
def index():
    if request.method == "POST":
        option = request.form.get("options")
        file = request.files["PDF"]
        file.save(r"C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\pdf_to_json\static\temp.pdf")
        file.close()
        if option == "1":
            return redirect(url_for("pdf_to_json.text"))
        if option == "2":
            return redirect(url_for("pdf_to_json.text2"))
        if option == "3":
            return redirect(url_for("pdf_to_json.text3"))
        if option == "4":
            return redirect(url_for("pdf_to_json.text4"))
        if option == "5":
            return redirect(url_for("pdf_to_json.text5"))
        if option == "6":
            return redirect(url_for("pdf_to_json.text6"))
        if option == "7":
            return redirect(url_for("pdf_to_json.text7"))
        if option == "8":
            return redirect(url_for("pdf_to_json.text8"))
    return render_template("pdf_to_json/index.html")

@project3.route("/text_from_pdf")
def text():
    file = open(r"C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\pdf_to_json\static\temp.pdf", "rb")
    ExtractTextInfoFromPDF(file)
    buffer = BytesIO()
    with open(r"C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\pdf_to_json\output\text_from_PDF.zip", "rb") as file:
        buffer.write(file.read())
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='text_from_pdf.zip', mimetype='application/zip')

@project3.route("/text_with_char_bounds")
def text2():
    file = open(r"C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\pdf_to_json\static\temp.pdf", "rb")
    ExtractTextInfoWithCharBoundsFromPDF(file)
    file.close
    buffer = BytesIO()
    with open(r"C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\pdf_to_json\output\text_info_with_char_bounds.zip", "rb") as file:
        buffer.write(file.read())
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='text_with_char_bounds.zip', mimetype='application/zip')

@project3.route("/text_table_info")
def text3():
    file = open(r"C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\pdf_to_json\static\temp.pdf", "rb")
    ExtractTextTableInfoFromPDF(file)
    buffer = BytesIO()
    with open(r"C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\pdf_to_json\output\text_with_table_info.zip", "rb") as file:
        buffer.write(file.read())
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='text_table_info.zip', mimetype='application/zip')

@project3.route("/text_table_info_with_char")
def text4():
    file = open(r"C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\pdf_to_json\static\temp.pdf", "rb")
    ExtractTextInfoWithCharBoundsFromPDF(file)
    buffer = BytesIO()
    with open(r"C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\pdf_to_json\output\text_table_info_with_char_bounds.zip", "rb") as file:
        buffer.write(file.read())
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='text_table_info_with_char_bounds.zip', mimetype='application/zip')

@project3.route("/6", methods=["POST"])
def text5():
    file = open(r"C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\pdf_to_json\static\temp.pdf", "rb")
    ExtractTextTableInfoWithFiguresTablesRenditionsFromPDF(file)
    buffer = BytesIO()
    with open(r"C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\pdf_to_json\output\extract_text_table_info_with_figures_tables_renditions.zip", "rb") as file:
        buffer.write(file.read())
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='extract_text_table_info_with_figures_tables_renditions.zip', mimetype='application/zip')

@project3.route("/7")
def text6():
    file = open(r"C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\pdf_to_json\static\temp.pdf", "rb")
    ExtractTextInfoFromPDF(file)
    buffer = BytesIO()
    with open(r"C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\pdf_to_json\output\extract_text_table_info_with_renditions.zip", "rb") as file:
        buffer.write(file.read())
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='text_table_info_with_renditions.zip', mimetype='application/zip')

@project3.route("/8")
def text7():
    file = open(r"C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\pdf_to_json\static\temp.pdf", "rb")
    ExtractTextTableInfoWithStylingFromPDF(file)
    buffer = BytesIO()
    with open(r"C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\pdf_to_json\output\extract_text_table_info_with_styling.zip", "rb") as file:
        buffer.write(file.read())
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='text_table_info_with_styling.zip', mimetype='application/zip')

@project3.route("/9")
def text8():
    file = open(r"C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\pdf_to_json\static\temp.pdf", "rb")
    ExtractTextTableInfoWithTableStructureFromPDF(file)
    buffer = BytesIO()
    with open(r"C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\pdf_to_json\output\extract_text_table_info_with_table_structure.zip", "rb") as file:
        buffer.write(file.read())
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='text_table_info_with_table_structure.zip', mimetype='application/zip')

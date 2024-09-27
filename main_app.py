import os
from flask import render_template
from app_factory import app, db




# Import and register blueprints
from Quresh_Database import project1
from EXCEL_TO_PDF_2 import project2
from pdf_to_json import project3

app.register_blueprint(project1, url_prefix="/excel_to_db")
app.register_blueprint(project2, url_prefix="/excel_to_db_02")
app.register_blueprint(project3, url_prefix="/PDF_TO_JSON")

@app.route("/")
def main_home():
    return render_template("index.html")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        try:
            os.makedirs(app.config['UPLOAD_FOLDER'])
        except OSError as e:
            print(f"Error creating upload folder: {e}")
    
    app.run(host="0.0.0.0", debug=True, port=5002)
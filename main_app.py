from flask import Flask, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Add this import
import os

app = Flask(__name__)
app.secret_key = 'ak47ma41'
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///C:\Users\Usama Ahmed\Documents\Quresh_Kitchen\Quresh_Database\instance\product_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get("task2_key")  # Change this to a secure random key
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Add this line to initialize Flask-Migrate


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
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host="0.0.0.0", debug=True, port=5001)

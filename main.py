import os
import secrets
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
# from Quresh_Database.database import db

migrate = Migrate()
cors = CORS()

basedir = os.path.abspath(os.path.dirname(__file__))

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = secrets.token_urlsafe(32)
    
    db_path = os.path.join(basedir, 'instance', 'product_database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path 
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
    app.config['EXCEL_TO_PDF_UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')

     # Logo configuration
    app.config['LOGO_FOLDER'] = basedir
    app.config['LOGO_FILENAME'] = 'logo.jpeg'  # Replace with your actual logo filename
    
    # # Initialize extensions with app
    # db.init_app(app)
    # migrate.init_app(app, db)
    # cors.init_app(app)
    
    # # Import and register blueprints
    # from Quresh_Database import project1
    from excel_to_pdf import project2
    from pdf_to_json import project3

    # app.register_blueprint(project1, url_prefix="/excel_to_db")
    app.register_blueprint(project2, url_prefix="/excel_to_pdf")
    app.register_blueprint(project3, url_prefix="/PDF_TO_JSON")
    
    @app.route("/", endpoint='main_home')
    def main_home():
       return render_template("home.html")

     # Logo serving route
    


    return app

app = create_app()

print("Registered routes:")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule.rule}")

if __name__ == '__main__':
    with app.app_context():
        # Code to be executed within the application context
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    app.run(host="0.0.0.0", debug=False, port=5100)

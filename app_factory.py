import os
import secrets
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS


# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()

def create_app(): 
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = secrets.token_urlsafe(32)
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'product_database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path 
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'uploads'

    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    
    return app

app = create_app() # Create the app instance here


from flask_migrate import Migrate
from main import create_app
from Quresh_Database.database import db

app = create_app()
migrate = Migrate(app, db)
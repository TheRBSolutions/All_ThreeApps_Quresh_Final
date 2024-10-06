from .database import db  # Import the db object from database.py

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    no = db.Column(db.Integer, unique=True, nullable=False)
    details = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    def __init__(self, **kwargs):
        super(Product, self).__init__(**kwargs)
        if not self.no:
            last_product = Product.query.order_by(Product.no.desc()).first()
            self.no = (last_product.no + 1) if last_product else 1

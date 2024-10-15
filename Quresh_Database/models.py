from .database import db  # Import the db object from database.py

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    no = db.Column(db.Integer, nullable=False)
    details = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.LargeBinary, nullable=True)  # This will store the image data
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    def __init__(self, **kwargs):
        super(Product, self).__init__(**kwargs)
        if not self.no:
            last_product = Product.query.order_by(Product.no.desc()).first()
            self.no = (last_product.no + 1) if last_product else 1

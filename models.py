from flask import Flask
from flask_jwt_extended import JWTManager
from datetime import datetime
from flask import json
from flask_wtf import FlaskForm
from flask_mongoengine import MongoEngine
from bson import ObjectId 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'koliinfotech5057ratna'
app.config['MONGODB_SETTINGS'] = {
    'db': 'ecommerce',
    'host': 'mongodb://127.0.0.1:27017/ecommerce'
}
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False

db = MongoEngine(app)


class User(db.Document):
    username = db.StringField(max_length=100, unique=True, required=True)
    email = db.EmailField(max_length=100, unique=True, required=True)
    phone_number = db.StringField(max_length=15, required=True)
    password = db.StringField(max_length=100, required=True)

    def __repr__(self):
        return f"User('{self.username}')"


class Customer(db.Document):
    name = db.StringField(max_length=100, required=True)
    email = db.StringField(max_length=100, required=True)

    def __repr__(self):
        return f"Customer('{self.name}', '{self.email}')"


class Product(db.Document):
    name = db.StringField(required=True, max_length=255)
    description = db.StringField()
    price = db.FloatField(required=True)
    quantity = db.IntField(required=True, default=0)
    category = db.StringField(max_length=50)
    brand = db.StringField(max_length=50)
    image_url = db.URLField()
    is_featured = db.BooleanField(default=False)
    created_at = db.DateTimeField(required=True, default=datetime.utcnow)

    def __repr__(self):
        return f"<Product(name={self.name}, price={self.price}, quantity={self.quantity}, category={self.category}, brand={self.brand})>"

    def to_dict(self):
        result = self.to_mongo().to_dict()
        result['id'] = str(result['_id'])
        del result['_id']
        return result

class Order(db.Document):
    customer = db.ReferenceField(User)
    product = db.ReferenceField(Product)
    quantity = db.IntField(required=True)
    order_date = db.DateTimeField(default=datetime.utcnow)
    status = db.StringField(max_length=50, default='Pending') 
    shipping_address = db.StringField(max_length=255) 
    total_price = db.FloatField(required=True)  

    def calculate_total_price(self):
        if self.product:
            product_price = self.product.price
            total_price = product_price * self.quantity
            self.total_price = total_price
            self.save()

    def mark_as_shipped(self):
        self.status = 'Shipped'
        self.save()

    def mark_as_delivered(self):
        self.status = 'Delivered'
        self.save()

    def __repr__(self):
        return f"Order('{self.customer.name}', '{self.product.name}', '{self.quantity}', '{self.order_date}', '{self.status}')"

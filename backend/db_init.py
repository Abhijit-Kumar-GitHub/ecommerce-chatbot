# ecommerce-chatbot/backend/db_init.py

import json
from db import db
from models import Product
from flask import Flask

# Path to your products JSON file
PRODUCTS_JSON_PATH = "../products/products.json"

# Path to your SQLite database
DB_PATH = "sqlite:///products.db"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DB_PATH
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

def load_products(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    with app.app_context():
        # Drop and recreate all tables
        db.drop_all()
        db.create_all()

        for item in data:
            product = Product(
                id=item["id"],
                name=item["name"],
                description=item["description"],
                price=item["price"],
                category=item["category"],
                image_url=item.get("image")  # Map JSON "image" to DB "image_url"
            )
            db.session.add(product)

        db.session.commit()
        print(f"Loaded {len(data)} products into the database.")

if __name__ == "__main__":
    load_products(PRODUCTS_JSON_PATH)
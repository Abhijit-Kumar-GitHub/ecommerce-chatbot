# ecommerce-chatbot/backend/db_init.py

import os
import json
from db import db
from models import Product
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Use DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

PRODUCTS_JSON_PATH = "../products/products.json"

def load_products(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    with app.app_context():
        # Only create tables — don't drop everything (to preserve users, chats, etc.)
        db.create_all()

        for item in data:
            existing = Product.query.get(item["id"])
            if not existing:
                product = Product(
                    id=item["id"],
                    name=item["name"],
                    description=item["description"],
                    price=item["price"],
                    category=item["category"],
                    image_url=item.get("image")
                )
                db.session.add(product)

        db.session.commit()
        print(f"Inserted or updated {len(data)} products into the database.")

if __name__ == "__main__":
    load_products(PRODUCTS_JSON_PATH)

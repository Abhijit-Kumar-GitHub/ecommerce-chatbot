# ecommerce-chatbot/backend/db_init.py

import json
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

from models import Product

# Define SQLite DB path
DB_PATH = "sqlite:///products.db"

# SQLAlchemy setup
Base = declarative_base()

# class Product(Base):                                  #commnented as now we have defined the class Product in models.py
#     __tablename__ = 'products'

#     id = Column(Integer, primary_key=True)
#     name = Column(String)
#     description = Column(String)
#     price = Column(Float)
#     category = Column(String)

# Create engine and session
engine = create_engine(DB_PATH)
Session = sessionmaker(bind=engine)
session = Session()

def load_products(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Clear old and create new table
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    for item in data:
        product = Product(
            id=item["id"],
            name=item["name"],
            description=item["description"],
            price=item["price"],
            category=item["category"]
        )
        session.add(product)

    session.commit()
    print(f"Loaded {len(data)} products into the database.")

if __name__ == "__main__":
    load_products("../products/products.json")

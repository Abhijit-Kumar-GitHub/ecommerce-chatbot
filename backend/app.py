# backend/app.py
import os
from flask import Flask
from dotenv import load_dotenv
from db import db
from routes.chat import chat_bp

load_dotenv()

app = Flask(__name__)

# Configure your DB URI here (example for SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///ecommerce_chatbot.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Register Blueprints
app.register_blueprint(chat_bp)

# Create tables before first request
@app.before_request
def create_tables():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)

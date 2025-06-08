# ecommerce-chatbot/backend/app.py
import os
from flask import Flask
from dotenv import load_dotenv
from db import db
from routes.chat import chat_bp
from routes.auth import auth_bp

load_dotenv()

app = Flask(__name__)

# Configure DB URI
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Register Blueprints
app.register_blueprint(chat_bp)
app.register_blueprint(auth_bp)

@app.route("/")
def index():
    return {"message": "E-commerce Chatbot API is running!"}

# Create tables before first request
@app.before_request
def create_tables():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


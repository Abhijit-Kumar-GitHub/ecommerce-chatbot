import os
from flask import Blueprint, request, jsonify
from functools import wraps
import jwt
from models import ChatSession, ChatMessage
from db import db
from datetime import datetime
import requests
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

chat_bp = Blueprint("chat", __name__)

# Config
CHROMA_PERSIST_DIR = "../products/chroma/"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "deepseek/deepseek-chat"
JWT_SECRET = os.getenv("JWT_SECRET_KEY")

embedding_function = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
vectorstore = Chroma(persist_directory=CHROMA_PERSIST_DIR, embedding_function=embedding_function)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # JWT token from Authorization header: "Bearer <token>"
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            current_user_id = data["user_id"]
        except Exception as e:
            return jsonify({"error": "Token is invalid", "details": str(e)}), 401

        return f(current_user_id, *args, **kwargs)
    return decorated

@chat_bp.route("/chat", methods=["POST"])
@token_required
def chat(current_user_id):
    data = request.get_json()
    user_query = data.get("query", "")

    if not user_query:
        return jsonify({"error": "Query not provided"}), 400

    # Find or create chat session
    session = ChatSession.query.filter_by(user_id=current_user_id).first()
    if not session:
        session = ChatSession(user_id=current_user_id)
        db.session.add(session)
        db.session.commit()

    # Save user message
    user_msg = ChatMessage(
        session_id=session.id,
        sender="user",
        content=user_query,
        timestamp=datetime.utcnow()
    )
    db.session.add(user_msg)
    db.session.commit()

    # Vector search for relevant product context
    relevant_docs = vectorstore.similarity_search(user_query, k=4)
    context = "\n".join([doc.page_content for doc in relevant_docs])

    prompt = f"""You are a helpful AI assistant for an electronics e-commerce store.
Based on the following product data, respond to the user's query.

--- Product Info ---
{context}
---------------------
User query: {user_query}
AI:"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/Abhijit-Kumar-GitHub/ecommerce-chatbot",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "You are a product expert assistant for electronics."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        ai_reply = response.json()["choices"][0]["message"]["content"]

        # Save AI response
        ai_msg = ChatMessage(
            session_id=session.id,
            sender="ai",
            content=ai_reply,
            timestamp=datetime.utcnow()
        )
        db.session.add(ai_msg)
        db.session.commit()

        return jsonify({"response": ai_reply})

    except requests.RequestException as e:
        return jsonify({"error": "OpenRouter API failed", "details": str(e)}), 500

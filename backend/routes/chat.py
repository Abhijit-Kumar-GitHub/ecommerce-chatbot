import os
import gc  # Add garbage collection
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

# Load embedding model and vector store only when needed
vectorstore = None
embedding_function = None

def get_vectorstore():
    global vectorstore, embedding_function
    if vectorstore is None:
        print("Initializing embedding model and vectorstore...")
        embedding_function = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        vectorstore = Chroma(persist_directory=CHROMA_PERSIST_DIR, embedding_function=embedding_function)
    return vectorstore



# ---------------- Token Check ----------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
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

# ---------------- Chat API ----------------
@chat_bp.route("/chat", methods=["POST"])
@token_required
def chat(current_user_id):
    data = request.get_json()
    user_query = data.get("query", "")
    session_id = data.get("session_id")

    if not user_query:
        return jsonify({"error": "Query not provided"}), 400

    # Use provided session or get latest
    if session_id:
        session = ChatSession.query.filter_by(id=session_id, user_id=current_user_id).first()
        if not session:
            return jsonify({"error": "Invalid session ID"}), 404
    else:
        session = ChatSession.query.filter_by(user_id=current_user_id).order_by(ChatSession.created_at.desc()).first()
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

    # Vector search
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

        return jsonify({
            "response": ai_reply,
            "session_id": session.id
        })

    except requests.RequestException as e:
        return jsonify({"error": "OpenRouter API failed", "details": str(e)}), 500

# ---------------- Reset Chat Session ----------------
@chat_bp.route("/chat/reset", methods=["POST"])
@token_required
def reset_chat(current_user_id):
    new_session = ChatSession(user_id=current_user_id)
    db.session.add(new_session)
    db.session.commit()

    return jsonify({
        "message": "New chat session started",
        "session_id": new_session.id,
        "created_at": new_session.created_at
    }), 201

# ---------------- List All Sessions ----------------
@chat_bp.route("/chat/sessions", methods=["GET"])
@token_required
def get_sessions(current_user_id):
    sessions = ChatSession.query.filter_by(user_id=current_user_id).order_by(ChatSession.created_at.desc()).all()
    result = [
        {
            "session_id": s.id,
            "created_at": s.created_at
        }
        for s in sessions
    ]
    return jsonify(result), 200

# ---------------- Get Messages by Session ----------------
@chat_bp.route("/chat/messages/<int:session_id>", methods=["GET"])
@token_required
def get_chat_messages(current_user_id, session_id):
    session = ChatSession.query.filter_by(id=session_id, user_id=current_user_id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404

    messages = ChatMessage.query.filter_by(session_id=session.id).order_by(ChatMessage.timestamp).all()
    result = [
        {
            "sender": msg.sender,
            "content": msg.content,
            "timestamp": msg.timestamp
        }
        for msg in messages
    ]
    return jsonify(result), 200

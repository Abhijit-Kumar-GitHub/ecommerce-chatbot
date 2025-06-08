
import os
import requests
from flask import Blueprint, request, jsonify
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
from datetime import datetime
from db import db
from models import Conversation

load_dotenv()

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# --------- Config ---------
CHROMA_PERSIST_DIR = "../products/chroma/"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "deepseek/deepseek-chat"
# --------------------------

embedding_function = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
vectorstore = Chroma(persist_directory=CHROMA_PERSIST_DIR, embedding_function=embedding_function)

@chat_bp.route('/message', methods=['POST'])
def chat():
    data = request.get_json()
    user_id = data.get('user_id')
    user_query = data.get('query')

    if not user_id or not user_query:
        return jsonify({"error": "user_id and query are required"}), 400

    # Vector search for relevant product info
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
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to contact OpenRouter", "details": str(e)}), 500

    ai_reply = response.json()["choices"][0]["message"]["content"]

    # Save conversation to DB
    conv = Conversation(
        user_id=user_id,
        user_message=user_query,
        bot_response=ai_reply,
        timestamp=datetime.utcnow()
    )
    db.session.add(conv)
    db.session.commit()

    return jsonify({
        "id": conv.id,
        "response": ai_reply,
        "timestamp": conv.timestamp.isoformat()
    })


@chat_bp.route('/history/<user_id>', methods=['GET'])
def get_history(user_id):
    conversations = Conversation.query.filter_by(user_id=user_id).order_by(Conversation.timestamp.asc()).all()
    history = [conv.to_dict() for conv in conversations]
    return jsonify({"history": history})

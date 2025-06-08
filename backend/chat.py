import os
from flask import Flask, request, jsonify
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# --------- Config ---------
CHROMA_PERSIST_DIR = "../products/chroma/"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") 
OPENROUTER_MODEL = "deepseek/deepseek-chat"
# --------------------------

app = Flask(__name__)

# Load embedding function and vectorstore
embedding_function = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
vectorstore = Chroma(persist_directory=CHROMA_PERSIST_DIR, embedding_function=embedding_function)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_query = data.get("query", "")
    
    if not user_query:
        return jsonify({"error": "Query not provided"}), 400

    # Perform vector search for relevant product info
    relevant_docs = vectorstore.similarity_search(user_query, k=4)
    context = "\n".join([doc.page_content for doc in relevant_docs])

    # Prepare OpenRouter prompt
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

    # Call OpenRouter
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)

    if response.status_code != 200:
        return jsonify({"error": "Failed to contact OpenRouter", "details": response.text}), 500

    ai_reply = response.json()["choices"][0]["message"]["content"]
    return jsonify({"response": ai_reply})


if __name__ == "__main__":
    app.run(debug=True)

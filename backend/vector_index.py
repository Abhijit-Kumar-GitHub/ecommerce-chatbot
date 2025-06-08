import os
import json
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings  # Updated import

# --------- Config ---------
PRODUCTS_JSON_PATH = "../products/products.json"
CHROMA_PERSIST_DIR = "../products/chroma/"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # Free, light, CPU-compatible
# --------------------------

# Load product data from JSON
with open(PRODUCTS_JSON_PATH, "r", encoding="utf-8") as f:
    products = json.load(f)

# Convert products into LangChain Documents
documents = []
for product in products:
    content = f"{product['name']}. {product['description']}. Price: ₹{product['price']}"
    documents.append(Document(page_content=content, metadata={"id": product["id"]}))

# Load sentence-transformers model (CPU-friendly)
print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
embedding_function = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

# Create Chroma vector store
print("Creating Chroma vectorstore...")
vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embedding_function,
    persist_directory=CHROMA_PERSIST_DIR
)

print(f"Vectorstore created and saved to {CHROMA_PERSIST_DIR}")
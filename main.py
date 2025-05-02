
import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from qdrant_client.models import SearchRequest
import requests

# Load environment variables
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama3-70b-8192" 
COLLECTION_NAME = "mental_health_data_solution"

# Initialize embedding model and Qdrant client
model = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(url=QDRANT_URL)
app = FastAPI()

# Input schema
class QueryRequest(BaseModel):
    question: str
    top_k: int = 3

# Function to call Groq API
def generate_answer_with_groq(context_texts: str, question: str) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "user",
                "content": f"Answer the question based on the context below:\n\nContext:\n{context_texts}\n\nQuestion: {question}"
            }
        ]
    }

    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        return "❌ Failed to get a response from the Groq model."

# Endpoint
@app.post("/chat")
async def chat(query: QueryRequest):
    query_vector = model.encode(query.question).tolist()

    search_result = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=query.top_k,
        with_payload=True
    )

    results = [
        {
            "score": round(hit.score, 4),
            "text": hit.payload.get("text", "")
        } for hit in search_result
    ]

    context = "\n\n".join([r["text"] for r in results])
    answer = generate_answer_with_groq(context, query.question) if context else "❌ No relevant context found."

    return {
        "query": query.question,
        "answer": answer,
        "top_matches": results
    }

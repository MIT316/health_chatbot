import os
import fitz
import requests
from dotenv import load_dotenv
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from huggingface_hub import HfApi
from tqdm import tqdm

# Load environment variables
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
HF_TOKEN = os.getenv("HF_TOKEN")
COLLECTION_NAME = "mental_health_data_solution"
model = SentenceTransformer("all-MiniLM-L6-v2")

def extract_text_from_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return []
    doc = fitz.open(pdf_path)
    return [page.get_text() for page in doc]

def load_hf_dataset():
    try:
        ds = load_dataset("Amod/mental_health_counseling_conversations", token=HF_TOKEN)
        return [f"Context: {item['Context']} Response: {item['Response']}" for item in ds["train"]]
    except Exception as e:
        print("❌ Error loading HF dataset:", e)
        return []

def create_collection(collection_name=COLLECTION_NAME, vector_size=384):
    url = f"{QDRANT_URL}/collections/{collection_name}"
    payload = {
        "vectors": {
            "size": vector_size,
            "distance": "Cosine"
        }
    }
    r = requests.put(url, json=payload)
    if r.status_code == 200:
        print(f"✅ Collection '{collection_name}' created.")
    elif r.status_code == 409:
        print(f"ℹ️ Collection '{collection_name}' already exists.")
    else:
        print(f"❌ Failed to create collection: {r.status_code} - {r.text}")

def upload_to_qdrant(texts, collection_name=COLLECTION_NAME, batch_size=500):
    print(f"🧠 Encoding {len(texts)} texts...")
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)
    
    headers = { "Content-Type": "application/json" }

    print("🚀 Uploading to Qdrant in batches...")
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        batch_embeddings = embeddings[i:i+batch_size]

        points = []
        for j, (text, emb) in enumerate(zip(batch_texts, batch_embeddings)):
            point = {
                "id": i + j,  # maintain unique IDs
                "vector": emb.tolist(),
                "payload": { "text": text }
            }
            points.append(point)

        payload = { "points": points }
        url = f"{QDRANT_URL}/collections/{collection_name}/points"

        r = requests.put(url, headers=headers, json=payload)
        if r.status_code in [200, 202]:
            print(f"✅ Uploaded batch {i // batch_size + 1} ({len(points)} points)")
        else:
            print(f"❌ Upload failed at batch {i // batch_size + 1}: {r.status_code} - {r.text}")
            break


if __name__ == "__main__":
    pdf_texts = extract_text_from_pdf("data/who_mentalhealth_dataset.pdf")
    hf_texts = load_hf_dataset()

    all_texts = pdf_texts + hf_texts
    if not all_texts:
        print("⚠️ No text data available to upload.")
    else:
        create_collection()
        upload_to_qdrant(all_texts)

from datasets import load_dataset
from dotenv import load_dotenv
import os

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

ds = load_dataset("Amod/mental_health_counseling_conversations", token=HF_TOKEN)
print(ds)

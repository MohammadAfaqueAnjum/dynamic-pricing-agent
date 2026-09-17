import os
import numpy as np
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from agents.state import PricingAgentState

load_dotenv()

embeddings_model = GoogleGenerativeAIEmbeddings(
    model="text-embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

def cosine_similarity(vec1: list, vec2: list) -> float:
    a, b = np.array(vec1), np.array(vec2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def sku_matcher_node(state: PricingAgentState) -> dict:
    our_title = state["title"]
    scraped_title = state.get("scraped_title") or state["title"]
    
    embeddings = embeddings_model.embed_documents([our_title, scraped_title])
    score = round(cosine_similarity(embeddings[0], embeddings[1]), 3)
    
    return {
        "sku_match_score": score,
        "is_valid_match": score >= 0.70
    }
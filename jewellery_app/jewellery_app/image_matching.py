"""
image_matching.py
-----------------
Image embedding and matching using DINOv2.
Fetches product images from Shopify URLs (not Storage).
"""

import json
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import torch
from transformers import AutoImageProcessor, AutoModel

import database


# Load DINOv2 model once at startup
_processor = None
_model = None

def _load_model():
    global _processor, _model
    if _model is None:
        print("Loading DINOv2 model...")
        _processor = AutoImageProcessor.from_pretrained('facebook/dinov2-small')
        _model = AutoModel.from_pretrained('facebook/dinov2-small')
        print("Model loaded.")
    return _processor, _model


def compute_embedding(image):
    """
    Compute DINOv2 embedding for a PIL Image.
    Returns a list (JSON-serializable).
    """
    processor, model = _load_model()
    
    # Ensure RGB
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize to DINOv2 input size
    image = image.resize((224, 224))
    
    # Process
    inputs = processor(images=image, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model(**inputs)
        embedding = outputs.last_hidden_state.mean(dim=1)[0].numpy()
    
    return embedding.tolist()


def normalize_embedding(emb):
    """Normalize embedding to unit length."""
    if isinstance(emb, str):
        emb = json.loads(emb)
    arr = np.array(emb)
    norm = np.linalg.norm(arr)
    if norm == 0:
        return arr.tolist()
    return (arr / norm).tolist()


def cosine_similarity(emb1, emb2):
    """Compute cosine similarity between two embeddings."""
    if isinstance(emb1, str):
        emb1 = json.loads(emb1)
    if isinstance(emb2, str):
        emb2 = json.loads(emb2)
    
    arr1 = np.array(emb1)
    arr2 = np.array(emb2)
    
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(np.dot(arr1, arr2) / (norm1 * norm2))


def find_matches(user_image, category_filter=None, top_k=20):
    """
    Find top-k matching products.
    
    Returns list of dicts:
      {
        "id": product_id,
        "code": product_code,
        "name": product_name,
        "image_url": shopify_url,  <-- Shopify URL, not Storage
        "confidence": 0–100,
        "website_url": link_to_shopify,
      }
    """
    # Compute embedding of user's image
    user_embedding = compute_embedding(user_image)
    user_embedding_norm = normalize_embedding(user_embedding)
    
    # Fetch all products
    all_products = database.get_all_products()
    
    if category_filter and category_filter != "All categories":
        all_products = [p for p in all_products if p.get("category") == category_filter]
    
    # Score each product
    scored = []
    for product in all_products:
        prod_emb = product.get("embedding")
        
        if not prod_emb:
            continue
        
        prod_emb_norm = normalize_embedding(prod_emb)
        score = cosine_similarity(user_embedding_norm, prod_emb_norm)
        
        scored.append({
            "id": product["id"],
            "code": product["product_code"],
            "name": product["product_name"],
            "image_url": product.get("image_url", ""),  # Shopify URL
            "similarity": score,
            "website_url": product.get("website_url", ""),
        })
    
    # Sort by similarity
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Convert to confidence (0–100 scale)
    matches = []
    for item in scored[:top_k]:
        conf = confidence_label(item["similarity"])
        matches.append({
            "id": item["id"],
            "code": item["code"],
            "name": item["name"],
            "image_url": item["image_url"],
            "confidence": conf["label"],
            "confidence_value": conf["value"],
            "website_url": item["website_url"],
        })
    
    return matches


def confidence_label(similarity_score):
    """
    Convert cosine similarity (0–1) to confidence label and percentage.
    """
    if similarity_score >= 0.82:
        return {"label": "✅ High confidence", "value": int(similarity_score * 100)}
    elif similarity_score >= 0.70:
        return {"label": "⚠️ Medium confidence", "value": int(similarity_score * 100)}
    else:
        return {"label": "❌ No reliable match", "value": int(similarity_score * 100)}

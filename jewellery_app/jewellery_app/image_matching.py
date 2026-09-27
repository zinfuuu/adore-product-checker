"""
image_matching.py
------------------
This is the "eye" of the app. It uses a free, open-source AI model called
CLIP to turn any jewellery photo into a "fingerprint": a list of ~512
numbers that represents what the image visually looks like.

Two photos of the same necklace - even one on a model and one on a plain
background - will produce fingerprints that are close to each other.
Two different products will produce fingerprints that are far apart.

We measure "closeness" with cosine similarity, a standard math technique
that outputs a score from -1 to 1. We convert that into a 0-100% score
that's easier for staff to read.

NOTE: The very first time this runs, it needs an internet connection to
download the CLIP model (about 600 MB, one-time only). After that it
works fully offline.
"""

import numpy as np
from PIL import Image

_model = None  # loaded once and reused (loading it is slow, so we cache it)


def get_model():
    """Load the CLIP model into memory (only happens once per app run)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("clip-ViT-B-32")
    return _model


def get_embedding(image_input):
    """
    Turn an image into a fingerprint (a list of numbers).
    'image_input' can be a file path (string) or an already-open PIL Image.
    Returns a plain Python list (so it can be saved as JSON in the database).
    """
    model = get_model()
    if isinstance(image_input, Image.Image):
        img = image_input.convert("RGB")
    else:
        img = Image.open(image_input).convert("RGB")
    embedding = model.encode(img, convert_to_numpy=True)
    return embedding.tolist()


def cosine_similarity(embedding_a, embedding_b):
    """
    Compare two fingerprints. Returns a score from -1 to 1
    (in practice, for real photos, usually between 0 and 1).
    """
    a = np.array(embedding_a, dtype=np.float32)
    b = np.array(embedding_b, dtype=np.float32)
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def similarity_to_percent(score):
    """
    Convert a raw cosine similarity score into a 0-100% display value.
    CLIP image-to-image scores for genuinely similar photos typically land
    in the 0.75-1.0 range and rarely go much below 0.5, so we stretch that
    range out to make the percentage meaningful and readable for staff.
    """
    stretched = (score - 0.5) / 0.5
    percent = max(0.0, min(1.0, stretched)) * 100
    return round(percent, 1)


def confidence_label(percent):
    """
    Map a percentage to a human-readable confidence label.

    NOTE: CLIP is a general-purpose visual model, not trained specifically
    on jewellery - visually similar but different pieces (same metal tone,
    similar layout) can still score deceptively high. These thresholds are
    intentionally strict so the app doesn't present a shaky guess as if it
    were certain. Staff should always glance at the photo, not just trust
    the percentage.
    """
    if percent >= 93:
        return "Very likely match", "success"
    elif percent >= 82:
        return "Possible match - please confirm visually", "warning"
    else:
        return "No reliable match", "error"


def find_matches(query_embedding, catalogue_products, top_n=5):
    """
    Compare one uploaded image's fingerprint against every catalogue product
    that has a stored fingerprint, and return the best matches sorted by
    similarity (best first).

    'catalogue_products' is a list of product dictionaries from the database,
    each expected to have an 'embedding' field (may be a JSON string or
    already a parsed list, depending on the database backend).
    """
    import json
    results = []
    for product in catalogue_products:
        if not product.get("embedding"):
            continue
        raw_embedding = product["embedding"]
        product_embedding = json.loads(raw_embedding) if isinstance(raw_embedding, str) else raw_embedding
        score = cosine_similarity(query_embedding, product_embedding)
        percent = similarity_to_percent(score)
        label, level = confidence_label(percent)
        results.append({
            **product,
            "similarity_percent": percent,
            "confidence_label": label,
            "confidence_level": level,
        })
    results.sort(key=lambda r: r["similarity_percent"], reverse=True)
    return results[:top_n]

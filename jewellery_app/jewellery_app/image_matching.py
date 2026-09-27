"""
image_matching.py
------------------
This is the "eye" of the app. It uses DINOv2, a free, open-source AI
vision model from Meta, to turn any jewellery photo into a "fingerprint":
a list of numbers that represents what the image visually looks like in
fine detail.

WHY DINOV2 INSTEAD OF CLIP
---------------------------
CLIP was trained to match images to *text captions* - it's good at
general semantic similarity ("this is a gold necklace"), but that means
two different gold necklaces with a similar general look can score
deceptively close together.

DINOv2 was trained differently: purely on images, with no text at all,
specifically to tell apart fine visual details between similar-looking
objects. This makes it much better suited to "is this the exact same
product" matching rather than "does this look like the same category of
thing" - which is exactly what SKU-level product matching needs.

We measure "closeness" the same way as before: cosine similarity (a
score from -1 to 1), converted into a 0-100% display value.

NOTE: The first time this runs, it needs internet access to download the
model (a few hundred MB, one-time only). After that it works offline.
"""

import numpy as np
import torch
from PIL import Image

_model = None
_processor = None

# Using the "small" DINOv2 variant rather than base/large - noticeably
# lighter on memory and CPU, which matters a lot on Streamlit Cloud's free
# tier (we've already hit crashes/throttling with heavier models here).
DINOV2_MODEL_NAME = "facebook/dinov2-small"


def get_model():
    """Load the DINOv2 model into memory (only happens once per app run)."""
    global _model, _processor
    if _model is None:
        from transformers import AutoImageProcessor, AutoModel
        _processor = AutoImageProcessor.from_pretrained(DINOV2_MODEL_NAME)
        _model = AutoModel.from_pretrained(DINOV2_MODEL_NAME)
        _model.eval()
    return _model, _processor


def get_embedding(image_input):
    """
    Turn an image into a fingerprint (a list of numbers).
    'image_input' can be a file path (string) or an already-open PIL Image.
    Returns a plain Python list (so it can be saved as JSON in the database).
    """
    model, processor = get_model()
    if isinstance(image_input, Image.Image):
        img = image_input.convert("RGB")
    else:
        img = Image.open(image_input).convert("RGB")

    inputs = processor(images=img, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)

    # The CLS token (first position) summarises the whole image - this is
    # the standard embedding to use for DINOv2 image retrieval/matching.
    embedding = outputs.last_hidden_state[:, 0, :][0]
    return embedding.numpy().tolist()


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

    NOTE: DINOv2's similarity scores are distributed differently than
    CLIP's were - this scaling formula is unchanged for now (per the
    "keep this phase simple" plan), but once you've tested a few real
    searches, the exact percentages you see may need retuning. That's a
    separate follow-up, not a sign something's broken.
    """
    stretched = (score - 0.5) / 0.5
    percent = max(0.0, min(1.0, stretched)) * 100
    return round(percent, 1)


def confidence_label(percent):
    """Map a percentage to a human-readable confidence label."""
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

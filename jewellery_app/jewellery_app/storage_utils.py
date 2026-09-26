"""
storage_utils.py
-----------------
Handles saving product photos to Supabase Storage instead of the local
disk. Local files (like the old /images folder) get wiped whenever the
Streamlit Cloud app sleeps, reboots, or is redeployed - storing photos in
Supabase Storage means they persist permanently, and are reachable by a
normal public URL so the app can display them directly.
"""

import os
import uuid

import requests
from PIL import Image

import database as db

BUCKET_NAME = "product-images"


def download_and_upload_image(image_url, product_code):
    """
    Download an image from `image_url`, verify it's a real image, and
    upload it to the Supabase Storage bucket.

    Returns (public_url, local_temp_path):
      - public_url: the permanent Supabase Storage URL to save in the
        database, or None on failure.
      - local_temp_path: a short-lived local copy (in /tmp) used only to
        compute the image's fingerprint right after this call.
    """
    try:
        response = requests.get(image_url, timeout=15)
        response.raise_for_status()

        ext = ".jpg"
        for candidate in [".jpg", ".jpeg", ".png", ".webp"]:
            if candidate in image_url.lower():
                ext = candidate
                break

        safe_code = "".join(c for c in product_code if c.isalnum() or c in "-_")
        filename = f"{safe_code}_{uuid.uuid4().hex[:6]}{ext}"
        temp_path = os.path.join("/tmp", filename)

        with open(temp_path, "wb") as f:
            f.write(response.content)

        # Verify it's a real, openable image before uploading it anywhere
        Image.open(temp_path).convert("RGB")

        client = db.get_client()
        content_type = f"image/{ext.strip('.').replace('jpg', 'jpeg')}"
        with open(temp_path, "rb") as f:
            client.storage.from_(BUCKET_NAME).upload(
                filename, f, {"content-type": content_type}
            )

        public_url = client.storage.from_(BUCKET_NAME).get_public_url(filename)
        return public_url, temp_path

    except Exception:
        return None, None

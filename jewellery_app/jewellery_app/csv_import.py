"""
csv_import.py
--------------
Handles importing your existing product catalogue from a CSV/Excel file.

Expected columns in the file (case-insensitive, order doesn't matter):
    Product Code       (required)
    Product Name       (required)
    Category           (optional)
    Website URL        (optional)
    Image URL          (optional - a web link to the product photo)

For each row, this file:
1. Downloads the image (if an Image URL is given) and saves it locally.
2. Generates the image's visual fingerprint using image_matching.py.
3. Saves everything into the database using database.py.

If a product code already exists, that row is skipped and reported,
so re-running an import is always safe (it won't create duplicates).
"""

import os
import uuid
import requests
import pandas as pd
from PIL import Image

import database as db
import image_matching as im

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")

# Accepts a few likely header spellings so real-world spreadsheets "just work"
COLUMN_ALIASES = {
    "product_code": ["product code", "code", "sku", "product_code"],
    "product_name": ["product name", "name", "product_name", "title"],
    "category": ["category", "type", "product_category"],
    "website_url": ["website url", "url", "product url", "link", "website_url"],
    "image_url": ["image url", "image", "image_link", "photo url", "image_url"],
}


def _find_column(df_columns, aliases):
    lower_map = {c.lower().strip(): c for c in df_columns}
    for alias in aliases:
        if alias in lower_map:
            return lower_map[alias]
    return None


def _download_image(url, product_code):
    """Download an image from a URL and save it locally. Returns the local path, or None on failure."""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        # Guess a safe file extension, default to .jpg
        ext = ".jpg"
        for candidate in [".jpg", ".jpeg", ".png", ".webp"]:
            if candidate in url.lower():
                ext = candidate
                break
        safe_code = "".join(c for c in product_code if c.isalnum() or c in "-_")
        filename = f"{safe_code}_{uuid.uuid4().hex[:6]}{ext}"
        local_path = os.path.join(IMAGES_DIR, filename)
        with open(local_path, "wb") as f:
            f.write(response.content)
        # Verify it's a real, openable image
        Image.open(local_path).convert("RGB")
        return local_path
    except Exception:
        return None


def import_csv(file_path, progress_callback=None):
    """
    Import products from a CSV or Excel file.
    'progress_callback', if given, is called after each row as
    progress_callback(current_index, total_rows, message) - used by the
    Streamlit page to show a live progress bar.

    Returns a summary dictionary with counts and a list of per-row messages.
    """
    if file_path.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)

    col_code = _find_column(df.columns, COLUMN_ALIASES["product_code"])
    col_name = _find_column(df.columns, COLUMN_ALIASES["product_name"])
    col_category = _find_column(df.columns, COLUMN_ALIASES["category"])
    col_url = _find_column(df.columns, COLUMN_ALIASES["website_url"])
    col_image = _find_column(df.columns, COLUMN_ALIASES["image_url"])

    if not col_code or not col_name:
        return {
            "success": False,
            "error": (
                "Could not find required columns. Your file must include a "
                "'Product Code' column and a 'Product Name' column."
            ),
        }

    total = len(df)
    added, skipped, failed = 0, 0, 0
    log = []

    for i, row in df.iterrows():
        code = str(row[col_code]).strip() if pd.notna(row[col_code]) else ""
        name = str(row[col_name]).strip() if pd.notna(row[col_name]) else ""

        if not code or not name:
            failed += 1
            log.append(f"Row {i + 2}: missing product code or name - skipped.")
            if progress_callback:
                progress_callback(i + 1, total, f"Skipped row {i + 2} (missing data)")
            continue

        if db.get_product_by_code(code):
            skipped += 1
            log.append(f"Row {i + 2}: product code '{code}' already exists - skipped.")
            if progress_callback:
                progress_callback(i + 1, total, f"Skipped {code} (already exists)")
            continue

        category = str(row[col_category]).strip() if col_category and pd.notna(row[col_category]) else ""
        website_url = str(row[col_url]).strip() if col_url and pd.notna(row[col_url]) else ""
        image_url = str(row[col_image]).strip() if col_image and pd.notna(row[col_image]) else ""

        local_image_path = ""
        embedding = None
        if image_url:
            local_image_path = _download_image(image_url, code)
            if local_image_path:
                try:
                    embedding = im.get_embedding(local_image_path)
                except Exception as e:
                    log.append(f"Row {i + 2}: image downloaded but fingerprinting failed ({e}).")
            else:
                log.append(f"Row {i + 2}: could not download image from {image_url}.")

        ok, message = db.add_product(
            product_code=code,
            product_name=name,
            category=category,
            website_url=website_url,
            image_path=local_image_path or "",
            status="Existing Product",
            embedding=embedding,
        )
        if ok:
            added += 1
            if progress_callback:
                progress_callback(i + 1, total, f"Added {code} - {name}")
        else:
            failed += 1
            log.append(f"Row {i + 2}: {message}")

    return {
        "success": True,
        "total_rows": total,
        "added": added,
        "skipped": skipped,
        "failed": failed,
        "log": log,
    }

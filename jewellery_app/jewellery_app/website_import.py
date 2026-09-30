"""
website_import.py
-----------------
Two-stage resumable import from Shopify:
  Stage 1: Fetch product metadata (fast, no images/embeddings)
  Stage 2: Download images, compute embeddings, store in DB

Images are NOT uploaded to Storage. We keep the original Shopify URLs.
"""

import os
import json
import time
from datetime import datetime
import shopify
import requests
from PIL import Image
from io import BytesIO

import database
import image_matching


SHOPIFY_SHOP_URL = "https://adorebypriyanka.com"
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")


def _get_shopify_session():
    """Create a Shopify API session."""
    shopify.ShopifyResource.set_site(f"{SHOPIFY_SHOP_URL}/admin/api/2024-01")
    session = shopify.Session(
        shop=SHOPIFY_SHOP_URL.replace("https://", "").replace(".com", ".myshopify.com"),
        access_token=SHOPIFY_ACCESS_TOKEN
    )
    shopify.ShopifyResource.activate_session(session)


def _with_retry(func, max_retries=3, delay=2):
    """Retry helper for transient failures."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
            time.sleep(delay)


def stage_1_fetch_metadata():
    """
    Fetch all products from Shopify and store metadata (name, code, URL).
    Skip if already done (tracked in import_state table).
    """
    state = database.get_state("stage_1_done")
    if state:
        print("Stage 1 already complete.")
        return

    _get_shopify_session()

    existing_codes = set(database.get_existing_product_codes())
    all_products = []
    page_count = 0

    print("Fetching all Shopify products...")
    
    for product in shopify.Product.find():
        page_count += 1
        
        code = product.handle or f"shopify_{product.id}"
        if code in existing_codes:
            continue

        # Get the first variant image, or product featured image
        image_url = None
        if hasattr(product, 'image') and product.image and hasattr(product.image, 'src'):
            image_url = product.image.src
        elif hasattr(product, 'images') and product.images:
            image_url = product.images[0].src

        all_products.append({
            "product_code": code,
            "product_name": product.title or "",
            "category": "",
            "website_url": f"{SHOPIFY_SHOP_URL}/products/{product.handle}",
            "image_url": image_url or "",
            "status": "active",
        })

        if len(all_products) % 100 == 0:
            print(f"Fetched {len(all_products)} products...")

    if all_products:
        database.add_products_bulk(all_products)
        print(f"Added {len(all_products)} products.")

    database.set_state("stage_1_done", "true")
    print("Stage 1 complete.")


def stage_2_compute_embeddings():
    """
    For each product missing an embedding:
      - Download image from Shopify URL
      - Compute DINOv2 embedding
      - Store embedding in DB
    
    Does NOT upload images to Storage. Uses Shopify URLs.
    """
    print("Stage 2: Computing embeddings...")

    while True:
        missing = database.get_products_missing_embedding(limit=50)
        
        if not missing:
            print("All products have embeddings!")
            break

        print(f"Processing {len(missing)} products...")

        for product in missing:
            try:
                product_id = product["id"]
                image_url = product.get("image_url", "")

                if not image_url:
                    print(f"  Product {product_id}: No image URL, skipping.")
                    continue

                # Download image from Shopify
                print(f"  Product {product_id}: Downloading image...")
                resp = requests.get(image_url, timeout=10)
                resp.raise_for_status()

                img = Image.open(BytesIO(resp.content))

                # Compute embedding
                print(f"  Product {product_id}: Computing embedding...")
                embedding = image_matching.compute_embedding(img)

                # Store embedding (keep image_url as-is)
                database.update_product(product_id, {"embedding": embedding})
                print(f"  Product {product_id}: Done.")

            except Exception as e:
                print(f"  Product {product_id}: ERROR — {e}")
                continue

        time.sleep(1)


def run_full_import():
    """Run both stages in sequence."""
    print("\n=== Starting full Shopify import ===\n")
    stage_1_fetch_metadata()
    print()
    stage_2_compute_embeddings()
    print("\n=== Import complete ===\n")


if __name__ == "__main__":
    run_full_import()

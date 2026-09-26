"""
website_import.py
------------------
Automatically imports products directly from your Shopify store
(www.adorebypriyanka.com), instead of requiring a manual CSV.

How this works (in simple terms):
Shopify online stores publish a public data feed of their products at
a web address like:
    https://www.adorebypriyanka.com/products.json

This isn't a secret API - it's a standard, public feature of every
Shopify store (used by apps, price-comparison tools, etc.) unless the
store owner has specifically disabled it. It gives us clean, structured
data for every product: name, price, category, images, and SKU/variant
codes - much more reliable than reading text off the webpage.

This file fetches that feed, page by page (Shopify limits each request
to 250 products), and turns each product into a row in our database,
downloading its main photo and generating its visual fingerprint.

NOTE: This needs to run somewhere with real internet access (your own
computer), not inside this sandboxed workspace.
"""

import time
import requests

import database as db
import image_matching as im
from csv_import import _download_image  # reuse the same image-download logic


def fetch_all_shopify_products(store_url, page_limit=250, max_pages=100, delay_seconds=0.5):
    """
    Download every product from a Shopify store's public product feed.
    'store_url' should be like 'https://www.adorebypriyanka.com'.
    Returns a list of raw Shopify product dictionaries.
    """
    store_url = store_url.rstrip("/")
    all_products = []

    for page in range(1, max_pages + 1):
        url = f"{store_url}/products.json?limit={page_limit}&page={page}"
        response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        data = response.json()
        products = data.get("products", [])

        if not products:
            break  # no more pages

        all_products.extend(products)
        time.sleep(delay_seconds)  # be polite to the server

    return all_products


def normalize_shopify_product(raw_product, store_url):
    """
    Convert a raw Shopify product JSON object into the simple fields our
    database expects: product_code, product_name, category, website_url,
    image_url.
    """
    store_url = store_url.rstrip("/")
    title = raw_product.get("title", "").strip()
    handle = raw_product.get("handle", "").strip()
    product_type = (raw_product.get("product_type") or "").strip()

    # Prefer a real SKU from the first variant that has one; otherwise
    # fall back to the product's URL "handle" (always unique) as the code.
    sku = ""
    variants = raw_product.get("variants") or []
    for variant in variants:
        if variant.get("sku"):
            sku = variant["sku"].strip()
            break
    product_code = sku if sku else handle.upper().replace("-", "_")[:40]

    images = raw_product.get("images") or []
    image_url = images[0]["src"] if images else ""

    website_url = f"{store_url}/products/{handle}" if handle else ""

    return {
        "product_code": product_code,
        "product_name": title,
        "category": product_type,
        "website_url": website_url,
        "image_url": image_url,
    }


def import_from_website(store_url, progress_callback=None):
    """
    Full import: fetch every product from the store, then add each one
    (with photo + fingerprint) to our local database.

    'progress_callback', if given, is called as
    progress_callback(current_index, total, message) for a live progress bar.

    Returns a summary dictionary, same shape as csv_import.import_csv().
    """
    try:
        raw_products = fetch_all_shopify_products(store_url)
    except Exception as e:
        return {
            "success": False,
            "error": (
                f"Could not reach the store's product feed ({e}). "
                "Double check the store URL, your internet connection, "
                "or try the CSV import instead."
            ),
        }

    if not raw_products:
        return {
            "success": False,
            "error": (
                "No products were found. The store's public product feed "
                "may be disabled, or the URL may be wrong."
            ),
        }

    total = len(raw_products)
    added, skipped, failed = 0, 0, 0
    log = []

    for i, raw_product in enumerate(raw_products):
        info = normalize_shopify_product(raw_product, store_url)
        code, name = info["product_code"], info["product_name"]

        if not code or not name:
            failed += 1
            log.append(f"Item {i + 1}: missing name or code - skipped.")
            if progress_callback:
                progress_callback(i + 1, total, "Skipped (missing data)")
            continue

        if db.get_product_by_code(code):
            skipped += 1
            log.append(f"Item {i + 1}: '{code}' already exists - skipped.")
            if progress_callback:
                progress_callback(i + 1, total, f"Skipped {code} (already exists)")
            continue

        local_image_path = ""
        embedding = None
        if info["image_url"]:
            local_image_path = _download_image(info["image_url"], code)
            if local_image_path:
                try:
                    embedding = im.get_embedding(local_image_path)
                except Exception as e:
                    log.append(f"Item {i + 1} ({code}): image fingerprinting failed ({e}).")
            else:
                log.append(f"Item {i + 1} ({code}): could not download image.")

        ok, message = db.add_product(
            product_code=code,
            product_name=name,
            category=info["category"],
            website_url=info["website_url"],
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
            log.append(f"Item {i + 1}: {message}")

    return {
        "success": True,
        "total_rows": total,
        "added": added,
        "skipped": skipped,
        "failed": failed,
        "log": log,
    }

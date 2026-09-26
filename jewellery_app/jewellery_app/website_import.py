"""
website_import.py
------------------
Automatically imports products directly from your Shopify store
(www.adorebypriyanka.com), instead of requiring a manual CSV.

WHY THIS FILE IS SPLIT INTO TWO STAGES
---------------------------------------
The old, single-step version of this import fetched every page of the
store's catalogue AND downloaded every photo AND computed every visual
fingerprint, all inside one call. For a catalogue of 4,000+ products,
that one call could run for well over an hour, use too much memory, and
crash the app. So the import is now two independent stages:

  STAGE 1 - fetch_and_save_metadata_page()
      Pulls ONE page (up to 250 products) of names/prices/categories/SKUs
      and the *URL* of each product's photo, and saves them to the
      database in ONE bulk request (not one-by-one), which is both fast
      and far less likely to trip a network error.

  STAGE 2 - generate_fingerprints_batch()
      Separately, works through whatever products are missing a visual
      fingerprint, downloading the photo, uploading it to permanent
      storage, and fingerprinting a small batch at a time.

Both stages record their progress in the database, not just in
Streamlit's session, so a page reload or an app reboot doesn't lose
your place.
"""

import requests

import database as db
import image_matching as im
from storage_utils import download_and_upload_image

STATE_KEY_PAGE = "shopify_import_next_page"
STATE_KEY_STORE_URL = "shopify_import_store_url"
STATE_KEY_DONE = "shopify_import_done"


def fetch_shopify_page(store_url, page, page_limit=250):
    """
    Fetch a single page of a Shopify store's public product feed.
    Returns the list of raw Shopify product dictionaries for that page
    (an empty list means there are no more pages).
    """
    store_url = store_url.rstrip("/")
    url = f"{store_url}/products.json?limit={page_limit}&page={page}"
    response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    data = response.json()
    return data.get("products", [])


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


# ---------------------------------------------------------------------------
# STAGE 1 - fast metadata import, one page at a time, bulk-inserted
# ---------------------------------------------------------------------------

def start_new_import(store_url):
    """Reset progress and begin a fresh Stage 1 import for this store URL."""
    db.set_state(STATE_KEY_STORE_URL, store_url)
    db.set_state(STATE_KEY_PAGE, 1)
    db.set_state(STATE_KEY_DONE, "0")


def get_import_progress():
    """Read back where Stage 1 currently is, so the page can resume correctly."""
    return {
        "store_url": db.get_state(STATE_KEY_STORE_URL, ""),
        "next_page": int(db.get_state(STATE_KEY_PAGE, 1)),
        "done": db.get_state(STATE_KEY_DONE, "0") == "1",
    }


def fetch_and_save_metadata_page(store_url, page, page_limit=250):
    """
    Do ONE page's worth of Stage 1 work: fetch up to `page_limit` products
    from Shopify, then save all the new ones in a single bulk database
    request (instead of one request per product).
    """
    try:
        raw_products = fetch_shopify_page(store_url, page, page_limit)
    except Exception as e:
        return {
            "success": False,
            "error": (
                f"Could not reach the store's product feed ({e}). "
                "Double check the store URL and your internet connection."
            ),
        }

    normalized = []
    failed = 0
    log = []

    for raw_product in raw_products:
        info = normalize_shopify_product(raw_product, store_url)
        if not info["product_code"] or not info["product_name"]:
            failed += 1
            log.append("An item was missing a name or code - skipped.")
            continue
        normalized.append(info)

    codes_on_page = [p["product_code"] for p in normalized]
    try:
        existing_codes = db.get_existing_product_codes(codes_on_page)
    except Exception as e:
        return {
            "success": False,
            "error": f"Could not check the database for existing products ({e}).",
        }

    to_insert = []
    skipped = 0
    for info in normalized:
        if info["product_code"] in existing_codes:
            skipped += 1
            continue
        to_insert.append({
            "product_code": info["product_code"],
            "product_name": info["product_name"],
            "category": info["category"],
            "website_url": info["website_url"],
            "image_path": "",
            "status": "Existing Product",
            "notes": "",
            "embedding": None,
            "image_url": info["image_url"],
        })

    try:
        added, insert_failed = db.add_products_bulk(to_insert)
        failed += insert_failed
    except Exception as e:
        return {
            "success": False,
            "error": f"Could not save products to the database ({e}).",
        }

    has_more = len(raw_products) == page_limit
    db.set_state(STATE_KEY_PAGE, page + 1)
    db.set_state(STATE_KEY_DONE, "0" if has_more else "1")

    return {
        "success": True,
        "page": page,
        "fetched": len(raw_products),
        "added": added,
        "skipped": skipped,
        "failed": failed,
        "has_more": has_more,
        "log": log,
    }


# ---------------------------------------------------------------------------
# STAGE 2 - background fingerprinting, a small batch at a time
# ---------------------------------------------------------------------------

def generate_fingerprints_batch(batch_size=25):
    """
    Process up to `batch_size` products that are missing a visual
    fingerprint: download each one's photo, upload it to permanent
    storage, and compute its embedding.
    """
    products = db.get_products_missing_embedding(limit=batch_size)

    processed, failed = 0, 0
    log = []

    for product in products:
        code = product["product_code"]
        image_url = product["image_url"]

        public_url, local_temp_path = download_and_upload_image(image_url, code)
        if not public_url:
            failed += 1
            log.append(f"{code}: could not download/upload image.")
            continue

        try:
            embedding = im.get_embedding(local_temp_path)
        except Exception as e:
            failed += 1
            log.append(f"{code}: fingerprinting failed ({e}).")
            continue

        db.update_product(product["id"], image_path=public_url, embedding=embedding)
        processed += 1

    return {
        "processed": processed,
        "failed": failed,
        "remaining": db.count_products_missing_embedding(),
        "log": log,
    }

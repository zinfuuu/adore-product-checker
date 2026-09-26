"""
database.py
------------
This file handles everything related to storing and retrieving product
information.

IMPORTANT CHANGE: this used to use a local SQLite file (data/jewellery.db).
That worked fine on your own computer, but on Streamlit Community Cloud,
local files are wiped every time the app sleeps from inactivity, reboots,
or gets redeployed - so the whole product catalogue could vanish without
warning. This version stores everything in Supabase (a free hosted
Postgres database) instead, so your data survives all of that.

Think of this file as the "filing cabinet" for the app: every other part
of the app asks this file to save, find, or update product records - the
rest of the app doesn't need to know or care that the storage moved.
"""

import os

import streamlit as st
from supabase import create_client, Client


def _get_secret(name):
    """Read a credential from Streamlit secrets (deployed app) or an
    environment variable (useful for local testing outside Streamlit)."""
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name)


SUPABASE_URL = _get_secret("SUPABASE_URL")
SUPABASE_KEY = _get_secret("SUPABASE_KEY")

_client = None


def get_client() -> Client:
    """Return a shared Supabase client, creating it on first use."""
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "Supabase credentials are missing. Add SUPABASE_URL and "
                "SUPABASE_KEY in your Streamlit app's Settings > Secrets."
            )
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def init_db():
    """
    Kept for compatibility with existing code (app.py calls db.init_db()
    on startup). The actual tables are created once, manually, via the
    Supabase SQL editor, so there's nothing to do here at runtime. This
    just checks the connection works.
    """
    get_client()


def add_product(product_code, product_name, category="", website_url="",
                 image_path="", status="Existing Product", notes="", embedding=None,
                 image_url=""):
    """
    Add a new product to the database.
    'image_path' is where the photo actually lives (a Supabase Storage
    public URL once uploaded).
    'image_url' is the original source URL (e.g. from Shopify) - saved
    even before the photo has been downloaded/fingerprinted, so a later
    background step can come back and finish the job.
    Returns (success: bool, message: str).
    """
    client = get_client()
    payload = {
        "product_code": product_code.strip(),
        "product_name": product_name.strip(),
        "category": category.strip() if category else "",
        "website_url": website_url.strip() if website_url else "",
        "image_path": image_path or "",
        "status": status,
        "notes": notes or "",
        "embedding": embedding,
        "image_url": image_url.strip() if image_url else "",
    }
    try:
        client.table("products").insert(payload).execute()
        return True, "Product added successfully."
    except Exception as e:
        if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
            return False, f"A product with code '{product_code}' already exists."
        return False, f"Could not add product: {e}"


def update_product(product_id, **fields):
    """
    Update one or more fields of an existing product.
    Usage: update_product(5, product_name="New Name", category="Rings")
    """
    if not fields:
        return False, "Nothing to update."
    client = get_client()
    try:
        client.table("products").update(fields).eq("id", product_id).execute()
        return True, "Product updated."
    except Exception as e:
        return False, f"Update failed: {e}"


def delete_product(product_id):
    get_client().table("products").delete().eq("id", product_id).execute()


def get_all_products(with_embedding_only=False):
    """Return every product as a list of dictionaries."""
    query = get_client().table("products").select("*").order("date_added", desc=True)
    res = query.execute()
    products = res.data or []
    if with_embedding_only:
        products = [p for p in products if p.get("embedding")]
    return products


def get_product_by_id(product_id):
    res = get_client().table("products").select("*").eq("id", product_id).execute()
    return res.data[0] if res.data else None


def get_product_by_code(product_code):
    res = get_client().table("products").select("*").eq("product_code", product_code).execute()
    return res.data[0] if res.data else None


def search_products(query):
    """Simple text search across product code, name, and category."""
    like = f"%{query}%"
    res = (
        get_client()
        .table("products")
        .select("*")
        .or_(f"product_code.ilike.{like},product_name.ilike.{like},category.ilike.{like}")
        .order("date_added", desc=True)
        .execute()
    )
    return res.data or []


def product_count():
    res = get_client().table("products").select("id", count="exact").execute()
    return res.count or 0


def get_products_missing_embedding(limit=50):
    """
    Products that have a known source image_url but don't have a visual
    fingerprint yet. This is the work queue for the background
    fingerprinting step (see website_import.py).
    """
    res = (
        get_client()
        .table("products")
        .select("*")
        .is_("embedding", "null")
        .not_.is_("image_url", "null")
        .neq("image_url", "")
        .order("id")
        .limit(limit)
        .execute()
    )
    return res.data or []


def count_products_missing_embedding():
    res = (
        get_client()
        .table("products")
        .select("id", count="exact")
        .is_("embedding", "null")
        .not_.is_("image_url", "null")
        .neq("image_url", "")
        .execute()
    )
    return res.count or 0


# ---------------------------------------------------------------------------
# Simple durable key/value storage, used to remember import progress so it
# survives page reloads, dropped connections, and app reboots.
# ---------------------------------------------------------------------------

def get_state(key, default=None):
    res = get_client().table("import_state").select("value").eq("key", key).execute()
    return res.data[0]["value"] if res.data else default


def set_state(key, value):
    get_client().table("import_state").upsert({"key": key, "value": str(value)}).execute()


def clear_state(key):
    get_client().table("import_state").delete().eq("key", key).execute()

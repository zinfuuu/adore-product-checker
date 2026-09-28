"""
database.py
------------
Stores and retrieves product information in Supabase (a hosted Postgres
database), so data survives app sleeps, reboots and redeploys.

NOTE ON THE 1000-ROW LIMIT: Supabase returns at most 1000 rows per
request. Any function that needs "everything" reads the table in pages of
1000 (see _fetch_all_rows) so that nothing beyond the first 1000 products
is silently ignored.
"""

import os
import time as _time

import streamlit as st
from supabase import create_client, Client


def _get_secret(name):
    """Read a credential from Streamlit secrets (deployed app) or an
    environment variable (GitHub Actions / local runs)."""
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


def _with_retry(func, *args, **kwargs):
    """Retry a Supabase call once if a transient network error happens."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if "RemoteProtocolError" in str(type(e)) or "Server disconnected" in str(e):
            _time.sleep(1)
            return func(*args, **kwargs)
        raise


def _fetch_all_rows(build_query, page_size=1000):
    """
    Fetch every row of a query by reading it in pages of `page_size`.
    `build_query` must return a fresh query that is ORDERED (so paging is
    stable and never skips or repeats rows).
    """
    all_rows = []
    start = 0
    while True:
        res = _with_retry(
            lambda: build_query().range(start, start + page_size - 1).execute()
        )
        rows = res.data or []
        all_rows.extend(rows)
        if len(rows) < page_size:
            break
        start += page_size
    return all_rows


def init_db():
    """
    Kept for compatibility (app.py calls db.init_db() on startup). The
    tables are created once via the Supabase SQL editor, so this just
    checks the connection works.
    """
    get_client()


def add_product(product_code, product_name, category="", website_url="",
                 image_path="", status="Existing Product", notes="", embedding=None,
                 image_url=""):
    """
    Add a new product to the database.
    'image_path' is where the photo lives (a Supabase Storage public URL).
    'image_url' is the original source URL (e.g. from Shopify), saved even
    before the photo has been fingerprinted.
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
            return False, f"A product

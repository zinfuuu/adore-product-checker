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
    data =

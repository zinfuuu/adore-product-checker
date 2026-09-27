"""
pages/4_Import_From_Website.py
-------------------------------
Two-stage, resumable import from your Shopify store's public product feed.

Stage 1 pulls product names/prices/categories/photo links - runs straight
through to completion in one click (lightweight, metadata only).

Stage 2 downloads photos and generates fingerprints - now auto-continues
in small batches until done, or until the connection needs a manual
nudge (just click Start/Continue again if it ever stops partway).

Progress is stored in Supabase, not locally, so a page reload or app
reboot never loses your place.
"""

import time

import streamlit as st

import database as db
import website_import as wi

st.set_page_config(page_title="Import From Website", page_icon="🌐")
db.init_db()

st.title("🌐 Import From Website")
st.caption("Pulls products directly from your store's public product feed - safe to stop and resume anytime.")

# ---------------------------------------------------------------------------
# STAGE 1 - fast metadata import (runs straight through in one click)
# ---------------------------------------------------------------------------
st.subheader("Stage 1 - Import product list")

progress = wi.get_import_progress()

default_store_url = progress["store_url"] or "https://www.adorebypriyanka.com"
store_url = st.text_input("Store URL", value=default_store_url)

col1, col2 = st.columns(2)
with col1:
    if progress["next_page"] > 1 and not progress["done"]:
        st.info(f"An import is in progress - next page to fetch: **{progress['next_page']}**")
    elif progress["done"]:
        st.success("Stage 1 finished - every page has been fetched.")
with col2:
    if st.button("🔄 Start a brand-new import (resets progress)"):
        wi.start_new_import(store_url)
        st.rerun()

button_label = "▶️ Start Import" if progress["next_page"] == 1 else "▶️ Continue Import"

if st.button(button_label, disabled=progress["done"]):
    if progress["next_page"] == 1:
        wi.start_new_import(store_url)

    status_box = st.empty()
    total_added, total_skipped, total_failed = 0, 0, 0

    while True:
        current = wi.get_import_progress()
        if current["done"]:
            break

        result = wi.fetch_and_save_metadata_page(current["store_url"], current["next_page"])
        if not result["success"]:
            st.error(result["error"])
            break

        total_added += result["added"]
        total_skipped += result["skipped"]
        total_failed += result["failed"]
        status_box.info(
            f"Page {result['page']}: fetched {result['fetched']}, "
            f"added {result['added']}, skipped {result['skipped']}. "
            f"(Running total - added: {total_added}, skipped: {total_skipped})"
        )

        if not result["has_more"]:
            st.success(f"Done! Added {total_added}, skipped {total_skipped} (already existed), failed {total_failed}.")
            break

        time.sleep(0.3)

    st.rerun()

st.write("")
st.divider()

# ---------------------------------------------------------------------------
# STAGE 2 - background fingerprinting (auto-continues until done or interrupted)
# ---------------------------------------------------------------------------
st.subheader("Stage 2 - Generate photo fingerprints")

remaining = db.count_products_missing_embedding()
st.write(f"Products waiting for a fingerprint: **{remaining}**")

batch_size = st.slider("Batch size per step", min_value=10, max_value=100, value=25, step=5)

if "stage2_running" not in st.session_state:
    st.session_state.stage2_running = False

fp_run_col, fp_stop_col = st.columns(2)
with fp_run_col:
    if st.button("▶️ Start / Continue Fingerprinting (auto-runs until done)", disabled=(remaining == 0)):
        st.session_state.stage2_running = True
        st.rerun()
with fp_stop_col:
    if st.button("⏹ Stop Fingerprinting"):
        st.session_state.stage2_running = False

fp_status_box = st.empty()

if st.session_state.stage2_running:
    if remaining == 0:
        st.session_state.stage2_running = False
        st.success("All products now have a fingerprint.")
    else:
        result = wi.generate_fingerprints_batch(batch_size=batch_size)
        fp_status_box.info(
            f"Processed {result['processed']}, failed {result['failed']}. "
            f"{result['remaining']} remaining."
        )
        if result["remaining"] == 0:
            st.session_state.stage2_running = False
            st.success("All products now have a fingerprint.")
        else:
            time.sleep(0.2)
            st.rerun()

"""
pages/4_Import_From_Website.py
-------------------------------
Two-stage, resumable import from your Shopify store's public product feed.

Stage 1 pulls product names/prices/categories/photo links, page by page.
Stage 2 works through a background queue, downloading photos and
generating fingerprints a small batch at a time.

Both stages show live progress and can be safely stopped and resumed -
closing this page, reloading it, or even rebooting the app won't lose
your place, since progress and data are stored in Supabase, not locally.
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
# STAGE 1 - fast metadata import
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

if "stage1_running" not in st.session_state:
    st.session_state.stage1_running = False

button_label = "▶️ Start Import" if progress["next_page"] == 1 else "▶️ Continue Import"
run_col, stop_col = st.columns(2)
with run_col:
    if st.button(button_label, disabled=progress["done"]):
        if progress["next_page"] == 1:
            wi.start_new_import(store_url)
        st.session_state.stage1_running = True
        st.rerun()
with stop_col:
    if st.button("⏹ Stop Import"):
        st.session_state.stage1_running = False

status_box = st.empty()

if st.session_state.stage1_running:
    progress = wi.get_import_progress()
    if progress["done"]:
        st.session_state.stage1_running = False
        st.rerun()
    else:
        result = wi.fetch_and_save_metadata_page(progress["store_url"], progress["next_page"])
        if not result["success"]:
            st.session_state.stage1_running = False
            st.error(result["error"])
        else:
            status_box.info(
                f"Page {result['page']}: fetched {result['fetched']}, "
                f"added {result['added']}, skipped {result['skipped']} (already existed)."
            )
            if not result["has_more"]:
                st.session_state.stage1_running = False
                st.success("Done! Every page has been imported.")
            else:
                time.sleep(0.2)
                st.rerun()

st.write("")
st.divider()

# ---------------------------------------------------------------------------
# STAGE 2 - background fingerprinting
# ---------------------------------------------------------------------------
st.subheader("Stage 2 - Generate photo fingerprints")

remaining = db.count_products_missing_embedding()
st.write(f"Products waiting for a fingerprint: **{remaining}**")

batch_size = st.slider("Batch size per step", min_value=10, max_value=100, value=25, step=5)

if "stage2_running" not in st.session_state:
    st.session_state.stage2_running = False

fp_run_col, fp_stop_col = st.columns(2)
with fp_run_col:
    if st.button("▶️ Start / Continue Fingerprinting", disabled=(remaining == 0)):
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

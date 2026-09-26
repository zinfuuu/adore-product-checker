"""
Product Catalogue page.

Three tabs:
  - Browse / Search: look through existing products
  - Add Product: add one product manually with a photo
  - Import from File: bulk import from CSV/Excel
"""

import os
import time
import uuid
import tempfile
import streamlit as st

import database as db
import image_matching as im
import csv_import as ci
import website_import as wi

st.set_page_config(page_title="Product Catalogue", page_icon="📖", layout="centered")
st.title("📖 Product Catalogue")

st.page_link("app.py", label="⬅ Back to Home")
st.write("")

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")

tab_browse, tab_add, tab_import, tab_website = st.tabs(
    ["🔎 Browse / Search", "➕ Add Product", "📂 Import from File", "🌐 Import from Website"]
)

# ---------------------------------------------------------------------------
# TAB 1: Browse / Search
# ---------------------------------------------------------------------------
with tab_browse:
    query = st.text_input("Search by code, name, or category", key="catalogue_search")
    products = db.search_products(query) if query else db.get_all_products()

    st.caption(f"{len(products)} product(s) found.")

    for p in products:
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                if p.get("image_path") and os.path.exists(p["image_path"]):
                    st.image(p["image_path"], width=100)
                else:
                    st.caption("No image")
            with c2:
                st.markdown(f"**{p['product_name']}**")
                st.caption(f"Code: `{p['product_code']}` | Category: {p.get('category') or '—'}")
                st.caption(f"Status: {p.get('status') or '—'} | Added: {p.get('date_added') or '—'}")
                if p.get("website_url"):
                    st.caption(f"[Website link]({p['website_url']})")
            with c3:
                with st.popover("Edit"):
                    edit_name = st.text_input("Name", value=p["product_name"], key=f"name_{p['id']}")
                    edit_category = st.text_input("Category", value=p.get("category") or "", key=f"cat_{p['id']}")
                    edit_url = st.text_input("Website URL", value=p.get("website_url") or "", key=f"url_{p['id']}")
                    edit_status = st.selectbox(
                        "Status", ["Existing Product", "New Product"],
                        index=0 if p.get("status") != "New Product" else 1,
                        key=f"status_{p['id']}",
                    )
                    save_col, delete_col = st.columns(2)
                    with save_col:
                        if st.button("Save", key=f"save_{p['id']}"):
                            db.update_product(
                                p["id"], product_name=edit_name, category=edit_category,
                                website_url=edit_url, status=edit_status,
                            )
                            st.success("Saved. Refresh to see changes.")
                    with delete_col:
                        if st.button("Delete", key=f"delete_{p['id']}"):
                            db.delete_product(p["id"])
                            st.success("Deleted. Refresh to see changes.")

# ---------------------------------------------------------------------------
# TAB 2: Add Product manually
# ---------------------------------------------------------------------------
with tab_add:
    st.write("Add a single product with its photo.")
    with st.form("manual_add_product", clear_on_submit=True):
        code = st.text_input("Product code / SKU *")
        name = st.text_input("Product name *")
        category = st.text_input("Category")
        website_url = st.text_input("Website URL (optional)")
        photo = st.file_uploader("Product photo", type=["jpg", "jpeg", "png", "webp"])
        submitted = st.form_submit_button("Add Product", type="primary")

        if submitted:
            if not code.strip() or not name.strip():
                st.error("Product code and product name are required.")
            else:
                local_path = ""
                embedding = None
                if photo:
                    os.makedirs(IMAGES_DIR, exist_ok=True)
                    safe_code = "".join(c for c in code if c.isalnum() or c in "-_")
                    filename = f"{safe_code}_{uuid.uuid4().hex[:6]}.jpg"
                    local_path = os.path.join(IMAGES_DIR, filename)
                    from PIL import Image
                    Image.open(photo).convert("RGB").save(local_path)
                    with st.spinner("Generating image fingerprint..."):
                        embedding = im.get_embedding(local_path)

                ok, message = db.add_product(
                    product_code=code, product_name=name, category=category,
                    website_url=website_url, image_path=local_path, embedding=embedding,
                )
                if ok:
                    st.success(message)
                else:
                    st.error(message)

# ---------------------------------------------------------------------------
# TAB 3: Import from CSV/Excel
# ---------------------------------------------------------------------------
with tab_import:
    st.write(
        "Upload a CSV or Excel file with your existing catalogue. "
        "Required columns: **Product Code**, **Product Name**. "
        "Optional: **Category**, **Website URL**, **Image URL**."
    )
    st.caption("Products whose code already exists in the catalogue will be skipped automatically - it's safe to re-run an import.")

    import_file = st.file_uploader("Choose CSV or Excel file", type=["csv", "xlsx", "xls"], key="import_uploader")

    if import_file and st.button("Start Import", type="primary"):
        # save to a temp file because our import function reads from disk
        suffix = os.path.splitext(import_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(import_file.getbuffer())
            tmp_path = tmp.name

        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(current, total, message):
            progress_bar.progress(current / total)
            status_text.text(f"({current}/{total}) {message}")

        with st.spinner("Importing..."):
            result = ci.import_csv(tmp_path, progress_callback=update_progress)

        os.remove(tmp_path)

        if not result["success"]:
            st.error(result["error"])
        else:
            st.success(
                f"Done! Added: {result['added']} | Skipped (duplicates): {result['skipped']} "
                f"| Failed: {result['failed']} out of {result['total_rows']} rows."
            )
            if result["log"]:
                with st.expander("Import details"):
                    for line in result["log"]:
                        st.text(line)

# ---------------------------------------------------------------------------
# TAB 4: Import directly from the website (Shopify store)
# ---------------------------------------------------------------------------
with tab_website:
    st.write(
        "Pull products directly from your live online store - no spreadsheet needed. "
        "This reads your store's public product listing, including product name, "
        "category, photo, and SKU (when set on the website)."
    )
    st.caption(
        "This can take a while for a large catalogue, since each product's photo "
        "is downloaded and analyzed. Products already in the catalogue (matching "
        "product code) are skipped automatically, so it's safe to re-run this "
        "later to pick up newly added products."
    )

    store_url = st.text_input(
        "Store website address", value="https://www.adorebypriyanka.com",
        help="The main address of your online store.",
    )

    WEBSITE_IMPORT_BATCH_SIZE = 150  # products processed per step, to stay light on memory

    col_start, col_cancel = st.columns([1, 1])
    with col_start:
        start_clicked = st.button("Start Website Import", type="primary")
    with col_cancel:
        cancel_clicked = st.button("Cancel") if st.session_state.get("website_import_state") else False

    if cancel_clicked:
        st.session_state.website_import_state = None
        st.info("Import cancelled. Anything already added is safely saved - you can resume later.")

    if start_clicked:
        with st.spinner("Connecting to your store..."):
            try:
                raw_products = wi.fetch_all_shopify_products(store_url)
            except Exception as e:
                raw_products = None
                st.error(
                    f"Could not reach the store's product feed ({e}). "
                    "Double check the store URL, your internet connection, or try the CSV import instead."
                )
        if raw_products is not None:
            if not raw_products:
                st.error(
                    "No products were found. The store's public product feed "
                    "may be disabled, or the URL may be wrong."
                )
            else:
                # Filter out products already in the catalogue UP FRONT, in one pass.
                # Without this, if most of the catalogue is already imported (e.g. from
                # a previous partial run), each batch would be almost instant "already
                # exists" skips, causing many auto-continues per second - which can
                # overwhelm the connection. Pre-filtering keeps every batch doing real,
                # similarly-paced work.
                already_skipped = 0
                new_raw_products = []
                filter_status = st.empty()
                filter_progress = st.progress(0)
                total_to_check = len(raw_products)
                for idx, raw_product in enumerate(raw_products):
                    info = wi.normalize_shopify_product(raw_product, store_url)
                    if info["product_code"] and db.get_product_by_code(info["product_code"]):
                        already_skipped += 1
                    else:
                        new_raw_products.append(raw_product)
                    # Update the UI regularly so the connection stays active during
                    # this pass and you can see it's actually working, not frozen.
                    if (idx + 1) % 100 == 0 or (idx + 1) == total_to_check:
                        filter_status.text(
                            f"Checking for duplicates: {idx + 1}/{total_to_check} "
                            f"({already_skipped} already in catalogue so far)"
                        )
                        filter_progress.progress((idx + 1) / total_to_check)
                filter_status.empty()
                filter_progress.empty()

                if not new_raw_products:
                    st.success(
                        f"All {len(raw_products)} products from the site are already in your catalogue. Nothing new to import."
                    )
                else:
                    st.session_state.website_import_state = {
                        "store_url": store_url,
                        "raw_products": new_raw_products,
                        # counts already skipped in the pre-filter pass so the final
                        # summary still reflects everything found on the site
                        "added": 0,
                        "skipped": already_skipped,
                        "failed": 0,
                        "log": [f"{already_skipped} product(s) were already in the catalogue (skipped during pre-check)."]
                        if already_skipped else [],
                        "index": 0,
                        "site_total": len(raw_products),
                    }

    state = st.session_state.get("website_import_state")
    if state:
        total_new = len(state["raw_products"])  # already-filtered, so every item here needs real work
        site_total = state.get("site_total", total_new)
        progress_bar = st.progress(state["index"] / total_new if total_new else 1.0)
        status_text = st.empty()

        if state["index"] < total_new:
            def update_progress(current, tot, message):
                status_text.text(f"({current}/{tot}) {message}")

            with st.spinner(
                f"Importing new products {state['index'] + 1}-{min(state['index'] + WEBSITE_IMPORT_BATCH_SIZE, total_new)} "
                f"of {total_new} (processing in small batches to avoid overloading the app)..."
            ):
                result = wi.import_from_website_batch(
                    state["store_url"], state["raw_products"], state["index"],
                    WEBSITE_IMPORT_BATCH_SIZE, progress_callback=update_progress,
                )

            state["added"] += result["added"]
            state["skipped"] += result["skipped"]
            state["failed"] += result["failed"]
            state["log"].extend(result["log"])
            state["index"] = result["next_index"]
            progress_bar.progress(state["index"] / total_new)

            if state["index"] < total_new:
                time.sleep(0.3)  # small pause between batches, easy on the connection
                st.rerun()  # automatically continue with the next batch
            else:
                st.success(
                    f"Done! Added: {state['added']} | Skipped (already existed): {state['skipped']} "
                    f"| Failed: {state['failed']} out of {site_total} products found on the site."
                )
                if state["log"]:
                    with st.expander("Import details"):
                        for line in state["log"]:
                            st.text(line)
        else:
            st.success(
                f"Done! Added: {state['added']} | Skipped (already existed): {state['skipped']} "
                f"| Failed: {state['failed']} out of {site_total} products found on the site."
            )

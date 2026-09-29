"""
Check New Stock page.

Use case: a new shipment arrives. Staff photograph an item to check whether
it's already a catalogue product before creating a duplicate entry. If no
good match is found, they can add it as a brand-new product right here.
"""

import os
import uuid
import streamlit as st
from PIL import Image

import database as db
import image_matching as im
import ui_theme
st.set_page_config(page_title="Check New Stock", page_icon="📥", layout="centered")
ui_theme.apply_theme()
st.title("📥 Check New Stock")
st.caption("Photograph a new item to check if it already exists in our catalogue.")

st.page_link("app.py", label="⬅ Back to Home")
st.write("")

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")

source = st.radio("Image source", ["Upload a photo", "Take a photo now"], horizontal=True, key="stock_source")

uploaded_image = None
if source == "Upload a photo":
    file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png", "webp"], key="stock_uploader")
    if file:
        uploaded_image = Image.open(file)
else:
    camera_file = st.camera_input("Take a photo", key="stock_camera")
    if camera_file:
        uploaded_image = Image.open(camera_file)

if uploaded_image:
    st.image(uploaded_image, caption="New item photo", width=300)

    if st.button("🔍 Check Against Catalogue", type="primary"):
        with st.spinner("Analyzing image..."):
            query_embedding = im.get_embedding(uploaded_image)
            st.session_state["stock_query_embedding"] = query_embedding
            st.session_state["stock_image_ready"] = True

    if st.session_state.get("stock_image_ready"):
        catalogue = db.get_all_products(with_embedding_only=True)
        matches = im.find_matches(st.session_state["stock_query_embedding"], catalogue, top_n=3) if catalogue else []

        best = matches[0] if matches else None
        strong_match = best is not None and best["similarity_percent"] >= 75

        st.write("---")
        if strong_match:
            st.warning(f"⚠️ Possible existing product - {best['similarity_percent']}% similarity ({best['confidence_label']})")
            bcol1, bcol2 = st.columns([1, 2])
            with bcol1:
                if best.get("image_path"):
                    try:
                        st.image(best["image_path"], width=180)
                    except Exception:
                        pass
            with bcol2:
                st.markdown(f"**Product name:** {best['product_name']}")
                st.markdown(f"**Product code:** `{best['product_code']}`")
                st.markdown(f"**Category:** {best.get('category') or '—'}")
                if best.get("website_url"):
                    st.markdown(f"**Product page:** [{best['website_url']}]({best['website_url']})")
            st.info("If this is indeed the same product, no need to add it again - just restock as usual.")

            if len(matches) > 1:
                with st.expander("See other possible matches"):
                    for m in matches[1:]:
                        st.markdown(f"- **{m['product_name']}** (`{m['product_code']}`) - {m['similarity_percent']}%")
        else:
            st.error("❌ No strong match found — this may be a new product.")

        st.write("---")
        with st.expander("➕ Add this as a new product", expanded=not strong_match):
            with st.form("add_new_stock_product"):
                new_code = st.text_input("Product code / SKU *")
                new_name = st.text_input("Product name *")
                new_category = st.text_input("Category")
                new_url = st.text_input("Website URL (optional)")
                new_notes = st.text_area("Notes (optional)")
                submitted = st.form_submit_button("Save New Product")

                if submitted:
                    if not new_code.strip() or not new_name.strip():
                        st.error("Product code and product name are required.")
                    else:
                        os.makedirs(IMAGES_DIR, exist_ok=True)
                        safe_code = "".join(c for c in new_code if c.isalnum() or c in "-_")
                        filename = f"{safe_code}_{uuid.uuid4().hex[:6]}.jpg"
                        local_path = os.path.join(IMAGES_DIR, filename)
                        uploaded_image.convert("RGB").save(local_path)

                        ok, message = db.add_product(
                            product_code=new_code,
                            product_name=new_name,
                            category=new_category,
                            website_url=new_url,
                            image_path=local_path,
                            status="New Product",
                            notes=new_notes,
                            embedding=st.session_state["stock_query_embedding"],
                        )
                        if ok:
                            st.success(f"✅ {message} It's now searchable in the catalogue.")
                            st.session_state["stock_image_ready"] = False
                        else:
                            st.error(message)

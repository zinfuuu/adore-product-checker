"""
Identify Product page.

Use case: a customer shows staff a screenshot from Instagram/website, or
staff photograph a piece a customer brought in. This page finds the closest
matching product(s) already in the catalogue.
"""

import streamlit as st
from PIL import Image

import database as db
import image_matching as im

st.set_page_config(page_title="Identify Product", page_icon="🔍", layout="centered")
st.title("🔍 Identify Product")
st.caption("Upload a photo or screenshot to search our catalogue.")

st.page_link("app.py", label="⬅ Back to Home")
st.write("")

# Optional category filter - narrowing the search pool to just one category
# (e.g. "Bracelet") meaningfully improves accuracy, since the AI model only
# has to tell apart items within that category instead of the whole store.
categories = db.get_distinct_categories()
category_choice = st.selectbox(
    "Category (optional, but recommended if known)",
    options=["All categories"] + categories,
    help="Narrowing this down helps the search avoid confusing similar-looking items from different categories.",
)

source = st.radio("Image source", ["Upload a photo/screenshot", "Take a photo now"], horizontal=True)

uploaded_image = None
if source == "Upload a photo/screenshot":
    file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png", "webp"])
    if file:
        uploaded_image = Image.open(file)
else:
    camera_file = st.camera_input("Take a photo")
    if camera_file:
        uploaded_image = Image.open(camera_file)

if uploaded_image:
    st.image(uploaded_image, caption="Image to search", width=300)

    if st.button("🔍 Search Catalogue", type="primary"):
        catalogue = db.get_all_products(with_embedding_only=True)

        if category_choice != "All categories":
            catalogue = [p for p in catalogue if p.get("category") == category_choice]

        if not catalogue:
            st.warning(
                "No products with photos were found for this category. "
                "Try 'All categories', or add products first from the Product Catalogue page."
            )
        else:
            with st.spinner("Analyzing image and comparing against catalogue..."):
                query_embedding = im.get_embedding(uploaded_image)
                matches = im.find_matches(query_embedding, catalogue, top_n=20)

            if not matches:
                st.error("No matches could be calculated.")
            else:
                best = matches[0]
                st.write("---")
                st.subheader("Best Match")

                if best["confidence_level"] == "success":
                    st.success(f"✅ {best['confidence_label']} - {best['similarity_percent']}% similarity")
                elif best["confidence_level"] == "warning":
                    st.warning(f"⚠️ {best['confidence_label']} - {best['similarity_percent']}% similarity")
                else:
                    st.error(f"❌ {best['confidence_label']} - {best['similarity_percent']}% similarity")
                    st.caption(
                        "No result was confident enough to trust automatically. "
                        "Compare the photos below yourself - the right one may still be among them."
                    )

                bcol1, bcol2 = st.columns([1, 2])
                with bcol1:
                    if best.get("image_path"):
                        try:
                            st.image(best["image_path"], width=200)
                        except Exception:
                            st.caption("(catalogue image unavailable)")
                with bcol2:
                    st.markdown(f"**Product name:** {best['product_name']}")
                    st.markdown(f"**Product code:** `{best['product_code']}`")
                    st.markdown(f"**Category:** {best.get('category') or '—'}")
                    st.markdown(f"**Status:** {best.get('status') or '—'}")
                    if best.get("website_url"):
                        st.markdown(f"**Product page:** [{best['website_url']}]({best['website_url']})")

                if len(matches) > 1:
                    st.write("---")
                    st.subheader("Other similar products")
                    st.caption("Always worth checking these too, especially if the best match wasn't confident.")
                    for m in matches[1:]:
                        c1, c2 = st.columns([1, 3])
                        with c1:
                            if m.get("image_path"):
                                try:
                                    st.image(m["image_path"], width=120)
                                except Exception:
                                    pass
                        with c2:
                            st.markdown(
                                f"**{m['product_name']}** (`{m['product_code']}`) "
                                f"- {m['similarity_percent']}% ({m['confidence_label']})"
                            )
                        st.write("")

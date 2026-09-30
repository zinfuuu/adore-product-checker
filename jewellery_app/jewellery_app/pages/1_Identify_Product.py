import streamlit as st
from PIL import Image
import io

import database
import image_matching
import ui_theme

# Apply theme
st.set_page_config(page_title="Identify Product", layout="centered")
ui_theme.apply_theme()

st.markdown("### Identify Product")
st.markdown("Upload a photo or screenshot to search our catalogue.")

# Back button
if st.button("← Back to Home"):
    st.switch_page("pages/app.py")

# Category filter
categories = database.get_distinct_categories()
category_list = ["All categories"] + sorted([c for c in categories if c])
selected_category = st.selectbox(
    "Category (optional, but recommended if known)",
    category_list,
    key="category_select"
)

# Image source
st.markdown("**Image source**")
image_source = st.radio(
    "Choose one:",
    ["Upload a photo/screenshot", "Take a photo now"],
    label_visibility="collapsed"
)

uploaded_file = None
if image_source == "Upload a photo/screenshot":
    uploaded_file = st.file_uploader(
        "Choose an image",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed"
    )
elif image_source == "Take a photo now":
    uploaded_file = st.camera_input("Take a photo", label_visibility="collapsed")

if uploaded_file:
    st.markdown("---")
    
    try:
        # Load image
        img = Image.open(uploaded_file)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Show what user uploaded
        st.markdown("**Your photo:**")
        st.image(img, width=300)
        
        # Search
        st.markdown("**Searching...**")
        category_filter = None if selected_category == "All categories" else selected_category
        matches = image_matching.find_matches(img, category_filter=category_filter, top_k=20)
        
        if not matches:
            st.warning("❌ No products found. Try a different photo or angle.")
        else:
            st.success(f"✅ Found {len(matches)} potential matches")
            st.markdown("---")
            
            for i, match in enumerate(matches, 1):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    if match["image_url"]:
                        try:
                            st.image(match["image_url"], width=150)
                        except:
                            st.text("(Image unavailable)")
                    else:
                        st.text("No image")
                
                with col2:
                    st.markdown(f"**#{i}**")
                    st.markdown(f"**{match['name']}**")
                    st.markdown(f"Code: `{match['code']}`")
                    st.markdown(f"{match['confidence']} ({match['confidence_value']}%)")
                    if match["website_url"]:
                        st.markdown(f"[View on website →]({match['website_url']})")
                
                st.divider()
    
    except Exception as e:
        st.error(f"Error processing image: {e}")

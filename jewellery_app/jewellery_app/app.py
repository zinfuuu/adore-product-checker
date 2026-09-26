"""
app.py
------
This is the starting point of the app. Run it with:
    streamlit run app.py

Streamlit automatically turns every file inside the 'pages' folder into
a separate screen, reachable from the sidebar menu. This file is just
the home screen with big, simple buttons for staff.
"""

import streamlit as st
import database as db

st.set_page_config(
    page_title="Jewellery Product Finder",
    page_icon="💎",
    layout="centered",
)

db.init_db()  # make sure the database file exists before anything else runs

st.title("💎 Jewellery Product Finder")
st.caption("Internal tool - find out if a product already exists in our catalogue")

count = db.product_count()
st.info(f"📦 Catalogue currently has **{count}** product(s).")

st.write("")
st.subheader("What would you like to do?")

col1, col2, col3 = st.columns(3)

with col1:
    st.page_link("pages/1_Identify_Product.py", label="🔍 Identify Product", use_container_width=True)
    st.caption("A customer showed you a photo - check if we sell it.")

with col2:
    st.page_link("pages/2_Check_New_Stock.py", label="📥 Check New Stock", use_container_width=True)
    st.caption("New shipment arrived - check if it's already in our catalogue.")

with col3:
    st.page_link("pages/3_Product_Catalogue.py", label="📖 Product Catalogue", use_container_width=True)
    st.caption("Browse, search, add, or import products.")

st.write("")
st.write("")
with st.expander("ℹ️ How this works"):
    st.write(
        "This app compares any photo you upload against the photos already "
        "saved in our own product catalogue - it never searches the internet. "
        "Matches are shown with a confidence percentage so you can judge how "
        "reliable each result is."
    )

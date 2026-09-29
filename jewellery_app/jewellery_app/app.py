"""
app.py
------
Home screen of the app. Streamlit turns every file inside the 'pages'
folder into a separate screen in the sidebar. This file is the welcome
screen with three big actions.
"""

import streamlit as st

import database as db
import ui_theme

st.set_page_config(page_title="Adore Scout", page_icon="💎", layout="centered")
ui_theme.apply_theme()
db.init_db()  # make sure the database connection works before anything else runs

# Hero artwork: (grid-area, shape). grid-area = row-start / col-start / row-end / col-end
_BLOCKS = [
    ("1 / 1 / 3 / 3", "sq"),
    ("1 / 3 / 4 / 4", "pill"),
    ("1 / 4 / 2 / 6", "pill"),
    ("1 / 6 / 3 / 7", "pill"),
    ("1 / 7 / 3 / 9", "sq"),
    ("2 / 4 / 4 / 5", "pill"),
    ("2 / 5 / 3 / 6", "dot"),
    ("3 / 1 / 6 / 2", "pill"),
    ("3 / 2 / 4 / 3", "dot"),
    ("3 / 5 / 4 / 7", "pill"),
    ("3 / 7 / 5 / 9", "sq"),
    ("4 / 2 / 6 / 4", "sq"),
    ("4 / 4 / 5 / 7", "pill"),
    ("5 / 4 / 7 / 5", "pill"),
    ("5 / 5 / 7 / 7", "sq"),
    ("5 / 7 / 6 / 8", "dot"),
    ("5 / 8 / 7 / 9", "pill"),
    ("6 / 1 / 7 / 4", "pill"),
    ("6 / 7 / 7 / 8", "dot"),
]

st.markdown(
    """
<style>
.hero-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  grid-template-rows: repeat(6, 1fr);
  gap: 7px;
  aspect-ratio: 8 / 6;
  margin: 0.4rem 0 2.2rem 0;
}
.hero-grid > div { background: #1C1B1A; }
.hero-grid .sq { border-radius: 24%; }
.hero-grid .pill { border-radius: 999px; }
.hero-grid .dot { border-radius: 50%; }

.eyebrow {
  text-align: center; letter-spacing: 0.42em; font-size: 0.66rem;
  font-weight: 600; text-transform: uppercase; color: #1C1B1A;
}
.hero-title {
  text-align: center; font-weight: 200 !important; letter-spacing: 0.22em;
  font-size: 2.2rem; text-transform: uppercase; color: #1C1B1A;
  margin: 0.5rem 0 0.7rem 0; padding: 0;
}
.hero-caption {
  text-align: center; letter-spacing: 0.32em; font-size: 0.62rem;
  text-transform: uppercase; color: #4A4642;
}
.stat { text-align: center; margin: 1.8rem 0 2rem 0; }
.stat-num {
  display: block; font-weight: 200; font-size: 3rem; letter-spacing: 0.08em;
  color: #1C1B1A; line-height: 1.05;
}
.stat-label {
  letter-spacing: 0.34em; font-size: 0.62rem; text-transform: uppercase;
  color: #4A4642;
}
.card-title {
  font-weight: 600; letter-spacing: 0.16em; font-size: 0.78rem;
  text-transform: uppercase; color: #1C1B1A; margin: 0 0 0.35rem 0;
}
.card-text { font-size: 0.85rem; color: #4A4642; margin: 0 0 0.9rem 0; line-height: 1.5; }
.footer-note {
  text-align: center; letter-spacing: 0.34em; font-size: 0.56rem;
  text-transform: uppercase; color: #6B665F; line-height: 2.1; margin-top: 2.4rem;
}
</style>
""",
    unsafe_allow_html=True,
)

hero_html = '<div class="hero-grid">' + "".join(
    f'<div class="{shape}" style="grid-area:{area}"></div>' for area, shape in _BLOCKS
) + "</div>"
st.markdown(hero_html, unsafe_allow_html=True)

try:
    count = f"{db.product_count():,}"
except Exception:
    count = "-"

st.markdown(
    '<div class="eyebrow">Adore by Priyanka</div>'
    '<h1 class="hero-title">Product Finder</h1>'
    '<div class="hero-caption">Find out if a piece is already in our catalogue</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="stat"><span class="stat-num">{count}</span>'
    '<span class="stat-label">Products in the catalogue</span></div>',
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown(
            '<div class="card-title">Identify Product</div>'
            '<div class="card-text">A customer showed you a photo. Check if we sell it.</div>',
            unsafe_allow_html=True,
        )
        st.page_link("pages/1_Identify_Product.py", label="Open", use_container_width=True)

with col2:
    with st.container(border=True):
        st.markdown(
            '<div class="card-title">Check New Stock</div>'
            '<div class="card-text">New shipment arrived. Check if it is already in our catalogue.</div>',
            unsafe_allow_html=True,
        )
        st.page_link("pages/2_Check_New_Stock.py", label="Open", use_container_width=True)

with col3:
    with st.container(border=True):
        st.markdown(
            '<div class="card-title">Product Catalogue</div>'
            '<div class="card-text">Browse, search, add, or import products.</div>',
            unsafe_allow_html=True,
        )
        st.page_link("pages/3_Product_Catalogue.py", label="Open", use_container_width=True)

st.write("")
with st.expander("How this works"):
    st.write(
        "This app compares any photo you upload against the photos already "
        "saved in our own product catalogue. It never searches the internet. "
        "Each result shows a similarity percentage. Treat it as a guide only, "
        "and always compare the photos yourself before deciding."
    )

st.markdown(
    '<div class="footer-note">Internal tool<br>Compares photos against our own catalogue only</div>',
    unsafe_allow_html=True,
)

"""
ui_theme.py
-----------
Shared look-and-feel for every page: warm grey paper, near-black ink,
thin wide-tracked type, black pill buttons.

Usage at the top of any page (right after st.set_page_config):
    import ui_theme
    ui_theme.apply_theme()
"""

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600&display=swap');

.stApp {
  background-image:
    url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='260' height='260'><g fill='%231C1B1A' fill-opacity='0.05'><rect x='10' y='10' width='60' height='60' rx='18'/><rect x='90' y='0' width='30' height='90' rx='15'/><circle cx='180' cy='40' r='22'/><rect x='150' y='90' width='90' height='30' rx='15'/><rect x='20' y='120' width='30' height='90' rx='15'/><rect x='80' y='150' width='60' height='60' rx='18'/><circle cx='200' cy='190' r='18'/></g></svg>"),
    url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.07 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
  background-repeat: repeat, repeat;
  background-size: 260px 260px, 180px 180px;
}
.stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp p, .stApp label, .stApp li, .stApp button,
.stApp a, .stApp input, .stApp textarea {
  font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif !important;
}
.stApp h1, .stApp h2, .stApp h3 {
  font-weight: 300 !important;
  letter-spacing: 0.04em;
}

.block-container { padding-top: 2.2rem; max-width: 820px; }

.stButton > button,
.stDownloadButton > button,
[data-testid="baseButton-primary"],
[data-testid="baseButton-secondary"],
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-secondary"] {
  border-radius: 999px;
  font-weight: 500;
  letter-spacing: 0.05em;
  padding: 0.45rem 1.4rem;
}

a[data-testid="stPageLink-NavLink"] {
  background: #1C1B1A;
  border-radius: 999px;
  justify-content: center;
  padding: 0.5rem 1rem;
}
a[data-testid="stPageLink-NavLink"]:hover { background: #3A3735; }
a[data-testid="stPageLink-NavLink"] p {
  color: #DCD8D2 !important;
  font-weight: 500;
  letter-spacing: 0.06em;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: #1C1B1A;
  border-radius: 26px;
}
div[data-baseweb="select"] > div,
.stTextInput input,
.stTextArea textarea { border-radius: 14px; }
[data-testid="stExpander"] details {
  border-radius: 20px;
  border-color: #1C1B1A;
}
</style>
"""


def apply_theme():
    st.markdown(_CSS, unsafe_allow_html=True)

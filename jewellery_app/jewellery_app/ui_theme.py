"""
ui_theme.py
-----------
Shared look-and-feel for every page: warm grey paper, near-black ink,
thin wide-tracked type, black pill buttons - plus the same rounded
pill/square/dot hero pattern used on the home page, faded and placed
behind the page content so every screen shares one consistent look.

Usage at the top of any page (right after st.set_page_config):
    import ui_theme
    ui_theme.apply_theme()
"""

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600&display=swap');
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
  background-color: #DCD8D2 !important;
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

.block-container { padding-top: 2.2rem; max-width: 820px; position: relative; z-index: 1; }

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
  background: rgba(255, 255, 255, 0.55);
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

# Same 19 blocks, same layout, as the home page hero - just rendered fixed
# in the background of every page instead of as page content.
_HERO_BLOCKS = [
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

_hero_blocks_html = "".join(
    f'<div class="{shape}" style="grid-area:{area}"></div>' for area, shape in _HERO_BLOCKS
)

_HERO_BG = f"""
<style>
.bg-hero-wrap {{
  position: fixed;
  inset: 0;
  z-index: 0;
  opacity: 0.19;
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  grid-template-rows: repeat(6, 1fr);
  gap: 10px;
  padding: 30px;
  pointer-events: none;
}}
.bg-hero-wrap > div {{ background: #1C1B1A; }}
.bg-hero-wrap .sq {{ border-radius: 24%; }}
.bg-hero-wrap .pill {{ border-radius: 999px; }}
.bg-hero-wrap .dot {{ border-radius: 50%; }}
</style>
<div class="bg-hero-wrap">{_hero_blocks_html}</div>
"""


def apply_theme():
    st.markdown(_CSS + _HERO_BG, unsafe_allow_html=True)

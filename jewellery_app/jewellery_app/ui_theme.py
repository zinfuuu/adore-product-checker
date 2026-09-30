"""
ui_theme.py
-----------
Shared look-and-feel for every page: burgundy background, cream cards,
black pill buttons, plus the pill/square/dot pattern behind the content,
and smooth mouse-wheel scrolling.

Usage at the top of any page (right after st.set_page_config):
    import ui_theme
    ui_theme.apply_theme()
"""

import streamlit as st
import streamlit.components.v1 as components


_CSS = """
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600&display=swap');


/* MAIN PAGE BACKGROUND */

html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
  background-color: #6B1425 !important;
}


/* GLOBAL FONT */

.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4,
.stApp p,
.stApp label,
.stApp li,
.stApp button,
.stApp a,
.stApp input,
.stApp textarea {
  font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif !important;
}

.stApp h1,
.stApp h2,
.stApp h3 {
  font-weight: 300 !important;
  letter-spacing: 0.04em;
}


/* CONTENT */

.block-container {
  padding-top: 2.2rem;
  max-width: 820px;
  position: relative;
  z-index: 1;
}


/* BUTTONS */

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
  transition: transform 0.3s ease, box-shadow 0.3s ease, background-color 0.3s ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}


/* PAGE NAVIGATION */

a[data-testid="stPageLink-NavLink"] {
  background: #1C1B1A;
  border-radius: 999px;
  justify-content: center;
  padding: 0.5rem 1rem;
  transition: transform 0.3s ease, background-color 0.3s ease, box-shadow 0.3s ease;
}

a[data-testid="stPageLink-NavLink"]:hover {
  background: #3A3735;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

a[data-testid="stPageLink-NavLink"] p {
  color: #DCD8D2 !important;
  font-weight: 500;
  letter-spacing: 0.06em;
}


/* CARDS */

div[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: #1C1B1A;
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.55);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}


/* INPUTS */

div[data-baseweb="select"] > div,
.stTextInput input,
.stTextArea textarea {
  border-radius: 14px;
  background-color: #F4EDE3 !important;
  color: #1C1B1A !important;
  border-color: #E6D5B8 !important;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}


/* FILE UPLOADER */

[data-testid="stFileUploader"] {
  max-width: 480px;
  margin: 0 auto;
}

[data-testid="stFileUploader"] section {
  background-color: #F4EDE3 !important;
  border-radius: 22px;
  border: 1.5px dashed #B08A3E !important;
  padding: 2rem 1.5rem !important;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

[data-testid="stFileUploaderDropzone"] {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  text-align: center !important;
  gap: 0.5rem;
}

[data-testid="stFileUploader"] section span,
[data-testid="stFileUploader"] section small {
  color: #4A4642 !important;
}

[data-testid="stFileUploaderDropzone"] svg {
  width: 34px;
  height: 34px;
}

[data-testid="stFileUploaderDropzone"] button {
  background-color: #1C1B1A !important;
  color: #F4EDE3 !important;
  border-radius: 999px !important;
  margin-top: 0.4rem;
}


/* TEXT */

.stRadio label p {
  color: #FBF6EE !important;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stCaptionContainer"] {
  color: #FBF6EE;
}


/* EXPANDERS */

[data-testid="stExpander"] details {
  border-radius: 20px;
  border-color: #1C1B1A;
}

/* SIDEBAR */

[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebarContent"] {
  background-color: #4A0E1A !important;
}

[data-testid="stSidebar"] a,
[data-testid="stSidebar"] a span,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] li {
  color: #FBF6EE !important;
}

[data-testid="stSidebarNavLink"][aria-current="page"],
[data-testid="stSidebar"] a[aria-current="page"] {
  background-color: rgba(251, 246, 238, 0.18) !important;
  border-radius: 12px;
}

[data-testid="stSidebarNavLink"]:hover,
[data-testid="stSidebar"] a:hover {
  background-color: rgba(251, 246, 238, 0.10) !important;
  border-radius: 12px;
}
/* FADE-IN ANIMATION */

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

[data-testid="stMetricContainer"] {
  animation: fadeInUp 0.6s ease-out;
}


/* ACCESSIBILITY */

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

</style>
"""


# HERO BACKGROUND PATTERN

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
    f'<div class="{shape}" style="grid-area:{area}"></div>'
    for area, shape in _HERO_BLOCKS
)

_HERO_BG = f"""
<style>

.bg-hero-wrap {{
  position: fixed;
  inset: 0;
  z-index: 0;
  opacity: 0.29;
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  grid-template-rows: repeat(6, 1fr);
  gap: 10px;
  padding: 30px;
  pointer-events: none;
}}

.bg-hero-wrap > div {{
  background: #1C1B1A;
}}

.bg-hero-wrap .sq {{ border-radius: 24%; }}
.bg-hero-wrap .pill {{ border-radius: 999px; }}
.bg-hero-wrap .dot {{ border-radius: 50%; }}

</style>

<div class="bg-hero-wrap">
  {_hero_blocks_html}
</div>
"""


# SMOOTH MOUSE-WHEEL SCROLL
# Runs inside a hidden component frame and controls the parent page's
# scrolling area (Streamlit scrolls an inner container, not the window).

_SMOOTH_SCROLL_JS = """
<script>
(function () {
  var parentWin = window.parent;
  var doc = parentWin.document;

  // Only install once, even though Streamlit reruns the script often.
  if (parentWin.__adoreSmoothScroll) { return; }
  parentWin.__adoreSmoothScroll = true;

  var EASE = 0.12;
  var current = 0;
  var target = 0;
  var frame = null;
  var scroller = null;

  function getScroller() {
    return doc.querySelector('[data-testid="stMain"]') ||
           doc.querySelector('section.main') ||
           doc.scrollingElement;
  }

  // If the mouse is over a scrollable inner box (dropdown list, table),
  // let the browser handle it normally.
  function insideInnerScrollable(el, root) {
    while (el && el !== root && el !== doc.body) {
      if (el.nodeType === 1) {
        var style = parentWin.getComputedStyle(el);
        var oy = style.overflowY;
        if ((oy === 'auto' || oy === 'scroll') &&
            el.scrollHeight > el.clientHeight + 1) {
          return true;
        }
      }
      el = el.parentNode;
    }
    return false;
  }

  function step() {
    current += (target - current) * EASE;
    if (Math.abs(target - current) < 0.5) {
      current = target;
    }
    scroller.scrollTop = current;
    if (current !== target) {
      frame = parentWin.requestAnimationFrame(step);
    } else {
      frame = null;
    }
  }

  doc.addEventListener('wheel', function (e) {
    if (e.ctrlKey) { return; }

    scroller = getScroller();
    if (!scroller || !scroller.contains(e.target)) { return; }
    if (insideInnerScrollable(e.target, scroller)) { return; }

    e.preventDefault();

    if (!frame) {
      current = scroller.scrollTop;
      target = current;
    }

    var delta = e.deltaY;
    if (e.deltaMode === 1) { delta *= 33; }

    var maxScroll = scroller.scrollHeight - scroller.clientHeight;
    target = Math.max(0, Math.min(target + delta, maxScroll));

    if (!frame) {
      frame = parentWin.requestAnimationFrame(step);
    }
  }, { passive: false });

})();
</script>
"""


# APPLY THEME

def apply_theme():
    st.markdown(_CSS + _HERO_BG, unsafe_allow_html=True)
    components.html(_SMOOTH_SCROLL_JS, height=0)

```python
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


/* =========================================================
   MAIN PAGE BACKGROUND
   ========================================================= */

html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
  background-color: #6B1425 !important;
}


/* =========================================================
   GLOBAL FONT
   ========================================================= */

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


/* =========================================================
   CONTENT
   ========================================================= */

.block-container {
  padding-top: 2.2rem;
  max-width: 820px;
  position: relative;
  z-index: 1;
}


/* =========================================================
   BUTTONS
   ========================================================= */

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

  transition:
    transform 0.3s ease,
    box-shadow 0.3s ease,
    background-color 0.3s ease;
}


.stButton > button:hover,
.stDownloadButton > button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}


/* =========================================================
   PAGE NAVIGATION
   ========================================================= */

a[data-testid="stPageLink-NavLink"] {
  background: #1C1B1A;
  border-radius: 999px;
  justify-content: center;
  padding: 0.5rem 1rem;

  transition:
    transform 0.3s ease,
    background-color 0.3s ease,
    box-shadow 0.3s ease;
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


/* =========================================================
   CARDS
   ========================================================= */

div[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: #1C1B1A;
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.55);

  transition:
    transform 0.3s ease,
    box-shadow 0.3s ease;
}


/* =========================================================
   INPUTS
   ========================================================= */

div[data-baseweb="select"] > div,
.stTextInput input,
.stTextArea textarea {
  border-radius: 14px;
  background-color: #F4EDE3 !important;
  color: #1C1B1A !important;
  border-color: #E6D5B8 !important;

  transition:
    border-color 0.3s ease,
    box-shadow 0.3s ease;
}


/* =========================================================
   FILE UPLOADER
   ========================================================= */

[data-testid="stFileUploader"] {
  max-width: 480px;
  margin: 0 auto;
}


[data-testid="stFileUploader"] section {
  background-color: #F4EDE3 !important;
  border-radius: 22px;
  border: 1.5px dashed #B08A3E !important;
  padding: 2rem 1.5rem !important;

  transition:
    transform 0.3s ease,
    box-shadow 0.3s ease;
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


/* =========================================================
   TEXT
   ========================================================= */

.stRadio label p {
  color: #FBF6EE !important;
}


[data-testid="stMarkdownContainer"] p,
[data-testid="stCaptionContainer"] {
  color: #FBF6EE;
}


/* =========================================================
   EXPANDERS
   ========================================================= */

[data-testid="stExpander"] details {
  border-radius: 20px;
  border-color: #1C1B1A;
}


/* =========================================================
   SMOOTH SCROLL
   ========================================================= */

html,
body {
  scroll-behavior: smooth;
}


/* =========================================================
   FADE-IN ANIMATION
   ========================================================= */

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}


/*
   Apply only to main content blocks.
   This gives the page a subtle entrance animation.
*/

[data-testid="stMetricContainer"] {
  animation: fadeInUp 0.6s ease-out;
}


/* =========================================================
   ACCESSIBILITY
   ========================================================= */

@media (prefers-reduced-motion: reduce) {

  html,
  body {
    scroll-behavior: auto;
  }

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


# =========================================================
# HERO BACKGROUND
# =========================================================

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

.bg-hero-wrap .sq {{
  border-radius: 24%;
}}

.bg-hero-wrap .pill {{
  border-radius: 999px;
}}

.bg-hero-wrap .dot {{
  border-radius: 50%;
}}

</style>

<div class="bg-hero-wrap">
  {_hero_blocks_html}
</div>
"""


# =========================================================
# SMOOTH MOUSE-WHEEL SCROLL
# =========================================================

_SMOOTH_SCROLL_JS = """
<script>

(function () {

    let currentScroll = window.scrollY;
    let targetScroll = window.scrollY;
    let animationFrame = null;

    const ease = 0.10;

    function smoothScroll() {

        currentScroll += (targetScroll - currentScroll) * ease;

        if (Math.abs(targetScroll - currentScroll) < 0.5) {
            currentScroll = targetScroll;
        }

        window.scrollTo(0, currentScroll);

        if (Math.abs(targetScroll - currentScroll) > 0.5) {
            animationFrame = requestAnimationFrame(smoothScroll);
        } else {
            animationFrame = null;
        }
    }


    window.addEventListener(
        "wheel",
        function (event) {

            /*
             * Don't interfere with zooming.
             */
            if (event.ctrlKey) {
                return;
            }


            /*
             * Prevent the browser's default
             * instant mouse-wheel movement.
             */
            event.preventDefault();


            /*
             * Add wheel movement to our target.
             */
            targetScroll += event.deltaY;


            /*
             * Keep target inside the page.
             */
            const maxScroll =
                document.documentElement.scrollHeight -
                window.innerHeight;

            targetScroll = Math.max(
                0,
                Math.min(targetScroll, maxScroll)
            );


            /*
             * Start smooth animation.
             */
            if (!animationFrame) {
                animationFrame =
                    requestAnimationFrame(smoothScroll);
            }

        },
        {
            passive: false
        }
    );


    /*
     * Keep values synchronized if Streamlit
     * changes the page height.
     */
    window.addEventListener(
        "scroll",
        function () {

            if (!animationFrame) {
                currentScroll = window.scrollY;
                targetScroll = window.scrollY;
            }

        },
        {
            passive: true
        }
    );

})();

</script>
"""


# =========================================================
# APPLY THEME
# =========================================================

def apply_theme():

    st.markdown(
        _CSS +
        _HERO_BG +
        _SMOOTH_SCROLL_JS,
        unsafe_allow_html=True
    )
```

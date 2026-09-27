"""
scheduled_sync.py
------------------
Runs the FULL catalogue sync end to end, in one go: every page of Stage 1
(product metadata), then every pending item in Stage 2 (photo download +
fingerprint). Meant to run automatically on a schedule (see
.github/workflows/daily_sync.yml), not from the Streamlit app itself.

Why a separate script instead of just using the Streamlit page:
  - It isn't tied to a browser tab or Streamlit session, so it can run
    for as long as it needs with no risk of looking "stuck," hitting a
    session timeout, or getting CPU-throttled the way Streamlit Cloud's
    free tier does.
  - Running it daily means any product that becomes visible on the
    website - even briefly - gets captured into the catalogue before it
    potentially goes out of stock and disappears from the public feed
    again. Once a product is in the catalogue, it stays there permanently.

Run it manually any time with:
    python scheduled_sync.py
"""

import sys
import time

import database as db
import website_import as wi

STORE_URL = "https://www.adorebypriyanka.com"


def run_stage1():
    print("=== Stage 1:

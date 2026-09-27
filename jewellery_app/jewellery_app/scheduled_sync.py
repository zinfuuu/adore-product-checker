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
    print("Stage 1: syncing product list")
    wi.start_new_import(STORE_URL)
    total_added = 0
    total_skipped = 0
    total_failed = 0

    while True:
        progress = wi.get_import_progress()
        if progress["done"]:
            break

        result = wi.fetch_and_save_metadata_page(progress["store_url"], progress["next_page"])
        if not result["success"]:
            print("ERROR:", result["error"])
            sys.exit(1)

        total_added += result["added"]
        total_skipped += result["skipped"]
        total_failed += result["failed"]
        print(
            "Page", result["page"], ":",
            "fetched", result["fetched"], ",",
            "added", result["added"], ",",
            "skipped", result["skipped"],
        )

        if not result["has_more"]:
            break
        time.sleep(0.3)

    print("Stage 1 complete. Added", total_added, "skipped", total_skipped, "failed", total_failed)


def run_stage2(batch_size=25):
    print("Stage 2: generating fingerprints")
    total_processed = 0
    total_failed = 0

    while True:
        remaining = db.count_products_missing_embedding()
        if remaining == 0:
            break

        result = wi.generate_fingerprints_batch(batch_size=batch_size)
        total_processed += result["processed"]
        total_failed += result["failed"]
        print(
            "Processed", result["processed"], ",",
            "failed", result["failed"], ",",
            result["remaining"], "remaining",
        )

        if result["remaining"] == 0:
            break

    print("Stage 2 complete. Processed", total_processed, "failed", total_failed)


if __name__ == "__main__":
    db.init_db()
    run_stage1()
    run_stage2()
    print("Sync finished.")

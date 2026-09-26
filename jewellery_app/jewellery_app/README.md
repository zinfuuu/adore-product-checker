# Jewellery Product Finder — Setup Guide (Phase 1 MVP)

This guide assumes you have never run a Python app before. Follow it step by step.

## What you're installing

- **Python** — the programming language the app is written in.
- A handful of **libraries** (listed in `requirements.txt`) — pre-built tools the app uses, including the free AI model that does the image matching.

The very first time you run the app, it will download the AI model (CLIP) automatically — about 600 MB, one-time only. After that, everything runs offline.

## Step 1: Install Python

1. Go to https://www.python.org/downloads/ and download the latest **Python 3** installer for your operating system.
2. Run the installer. **On Windows, tick the box "Add Python to PATH"** before clicking Install — this step is easy to miss but important.
3. To check it worked, open a terminal (Command Prompt on Windows, Terminal on Mac) and type:
   ```
   python --version
   ```
   You should see something like `Python 3.12.x`.

## Step 2: Get the app files onto your computer

Copy the whole `jewellery_app` folder (which I've given you) onto your computer — e.g. onto your Desktop.

## Step 3: Open a terminal inside the folder

- **Windows:** open the `jewellery_app` folder in File Explorer, click the address bar, type `cmd`, press Enter.
- **Mac:** right-click the `jewellery_app` folder → "New Terminal at Folder" (or open Terminal and type `cd ` followed by dragging the folder in).

## Step 4: Create a clean workspace (a "virtual environment")

This keeps the app's tools separate from anything else on your computer. Copy-paste these commands one at a time:

**Windows:**
```
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```
python3 -m venv venv
source venv/bin/activate
```

You'll know it worked because you'll see `(venv)` appear at the start of your terminal line.

## Step 5: Install the required tools

```
pip install -r requirements.txt
```

This will take a few minutes the first time (it's downloading things like the AI model library). This step needs an internet connection.

## Step 6: Run the app

```
streamlit run app.py
```

A browser tab should open automatically at `http://localhost:8501` showing the app. If it doesn't open automatically, copy that address into your browser.

**To use it on your phone/tablet in the store:** make sure the phone is on the same WiFi network as the computer running the app, then look at the terminal output for a line like `Network URL: http://192.168.x.x:8501` — open that address on the phone's browser.

## Step 7: Try it out

**Fastest way to get real data in:** Go to **Product Catalogue → Import from Website**, leave the address as `https://www.adorebypriyanka.com` (or change it if needed), and click **Start Website Import**. This pulls your products directly from your live store — name, category, photo, and SKU (if set on the website) — no spreadsheet needed. It downloads each product's photo and analyzes it, so a full catalogue (1000+ products, per your store's listing) will take a while the first time — that's normal, and it's safe to stop and re-run later since already-imported products are skipped.

Other ways to try it:
1. **Product Catalogue → Import from File** — import `sample_products.csv` (included) to see how CSV import works. It uses fake image URLs, so image download will fail for those rows — that's expected; use your own file with real image links for real data.
2. **Product Catalogue → Add Product** — manually add one product with a real photo.
3. **Identify Product** — upload a photo of a product you've already imported (or a similar one) and click Search — it should come back as a strong match.

### A note on product codes from the website import

Your website doesn't necessarily show a SKU/product code for every item. When a product has one set up on Shopify, we use it. When it doesn't, we generate a code from the product's web page name instead (e.g. `AURA_NECKPIECE_COPY`), so every product still gets a unique, stable code. You can always rename any product's code later from **Product Catalogue → Browse/Search → Edit**.

## Stopping the app

Go back to the terminal window and press `Ctrl + C`.

## Restarting later

Every time you want to run the app again, open a terminal in the folder and run:

**Windows:** `venv\Scripts\activate` then `streamlit run app.py`
**Mac:** `source venv/bin/activate` then `streamlit run app.py`

## Your data

- Product information is stored in `data/jewellery.db` — a single file. **Back this up regularly** (just copy the file somewhere safe, e.g. Google Drive).
- Product photos are stored in the `images/` folder — back this up too.

## What's next (not built yet)

This is the Phase 1 MVP: catalogue storage, CSV import, manual add, photo-based search, and the restock-check flow. Not yet included (for later phases once this is working well for you):
- Staff login / accounts
- Multiple jewellery items detected in a single photo
- Automatic sync from your website (instead of manual CSV import)
- Cloud hosting so multiple staff can use it from different devices without needing the same computer running
- Fine-tuning the similarity percentage thresholds based on real results from your store

Let me know once you've got this running and tried it with a few real products — we'll review how well the matching performs on your actual jewellery photos and adjust from there before adding the next features.

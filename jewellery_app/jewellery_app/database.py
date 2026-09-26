"""
database.py
------------
This file handles everything related to storing and retrieving product
information. It uses SQLite, which is just a single file on disk
(data/jewellery.db) - no separate database server needed.

Think of this file as the "filing cabinet" for the app: every other
part of the app asks this file to save, find, or update product records.
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "jewellery.db")


def get_connection():
    """Open a connection to the database file (creates it if it doesn't exist)."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name, e.g. row["product_name"]
    return conn


def init_db():
    """Create the products table if it doesn't already exist. Safe to call every time the app starts."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            category TEXT,
            website_url TEXT,
            image_path TEXT,
            status TEXT DEFAULT 'Existing Product',
            date_added TEXT,
            notes TEXT,
            embedding TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_product(product_code, product_name, category="", website_url="",
                 image_path="", status="Existing Product", notes="", embedding=None):
    """
    Add a new product to the database.
    'embedding' is the image's visual fingerprint (a list of numbers) - it gets
    stored as a JSON text string so it fits neatly into a normal database column.
    Returns (success: bool, message: str).
    """
    conn = get_connection()
    try:
        embedding_json = json.dumps(embedding) if embedding is not None else None
        conn.execute("""
            INSERT INTO products
                (product_code, product_name, category, website_url, image_path,
                 status, date_added, notes, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product_code.strip(), product_name.strip(), category.strip(),
            website_url.strip(), image_path, status,
            datetime.now().strftime("%Y-%m-%d %H:%M"), notes, embedding_json
        ))
        conn.commit()
        return True, "Product added successfully."
    except sqlite3.IntegrityError:
        return False, f"A product with code '{product_code}' already exists."
    finally:
        conn.close()


def update_product(product_id, **fields):
    """
    Update one or more fields of an existing product.
    Usage: update_product(5, product_name="New Name", category="Rings")
    """
    if not fields:
        return False, "Nothing to update."
    conn = get_connection()
    try:
        if "embedding" in fields and fields["embedding"] is not None:
            fields["embedding"] = json.dumps(fields["embedding"])
        columns = ", ".join(f"{key} = ?" for key in fields.keys())
        values = list(fields.values()) + [product_id]
        conn.execute(f"UPDATE products SET {columns} WHERE id = ?", values)
        conn.commit()
        return True, "Product updated."
    except sqlite3.IntegrityError:
        return False, "Update failed - product code may already be in use."
    finally:
        conn.close()


def delete_product(product_id):
    conn = get_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


def get_all_products(with_embedding_only=False):
    """Return every product as a list of dictionaries."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products ORDER BY date_added DESC").fetchall()
    conn.close()
    products = [dict(row) for row in rows]
    if with_embedding_only:
        products = [p for p in products if p.get("embedding")]
    return products


def get_product_by_id(product_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_product_by_code(product_code):
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE product_code = ?", (product_code,)).fetchone()
    conn.close()
    return dict(row) if row else None


def search_products(query):
    """Simple text search across product code, name, and category."""
    conn = get_connection()
    like = f"%{query}%"
    rows = conn.execute("""
        SELECT * FROM products
        WHERE product_code LIKE ? OR product_name LIKE ? OR category LIKE ?
        ORDER BY date_added DESC
    """, (like, like, like)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def product_count():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    conn.close()
    return count

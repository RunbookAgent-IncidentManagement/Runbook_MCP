#!/usr/bin/env python
"""Seed demo products into the database."""
import sys, os
sys.path.insert(0, "/home/user/ecommerce-platform/backend/product_service")

from sqlalchemy.orm import Session
from decimal import Decimal
import uuid

try:
    from backend.shared.database import SessionLocal
    from app.models import Product
except Exception:
    from database import SessionLocal
    from models import Product

def seed():
    try:
        db = SessionLocal()
        try:
            existing = db.query(Product).first()
            if existing:
                print("Data exists, skip seed.")
                return
            products = [
                {"name":"Silk Evening Gown","description":"Luxurious midnight silk evening gown.","price":Decimal("389.00"),"category":"Fashion","sku":"FASH-001","image_url":"/products/fashion-gown.jpg","stock_quantity":12,"status":"available"},
                {"name":"Wireless Noise-Canceling Headphones","description":"Premium over-ear headphones with 40-hour battery.","price":Decimal("349.99"),"category":"Electronics","sku":"ELEC-001","image_url":"/products/electronics-headphones.jpg","stock_quantity":45,"status":"available"},
                {"name":"Organic Rose Serum","description":"Anti-aging facial serum with organic rose extract.","price":Decimal("89.50"),"category":"Cosmetics","sku":"COSM-001","image_url":"/products/cosmetics-serum.jpg","stock_quantity":120,"status":"available"},
                {"name":"Artisan Leather Tote","description":"Handcrafted Italian full-grain leather tote bag.","price":Decimal("425.00"),"category":"Fashion","sku":"FASH-002","image_url":"/products/fashion-tote.jpg","stock_quantity":8,"status":"available"},
                {"name":"Smart Mirror Pro","description":"Interactive smart mirror with fitness tracking.","price":Decimal("599.00"),"category":"Electronics","sku":"ELEC-002","image_url":"/products/electronics-mirror.jpg","stock_quantity":15,"status":"available"},
                {"name":"Luxury Bath Gift Set","description":"Curated spa gift set with lavender salts, body scrub, silk eye mask and candle.","price":Decimal("129.99"),"category":"Cosmetics","sku":"COSM-002","image_url":"/products/cosmetics-bath.jpg","stock_quantity":60,"status":"available"},
                {"name":"Minimalist Silk Scarf","description":"Hand-painted 100% mulberry silk scarf with geometric patterns.","price":Decimal("145.00"),"category":"Fashion","sku":"FASH-003","image_url":"/products/fashion-scarf.jpg","stock_quantity":30,"status":"available"},
                {"name":"Premium Yoga Mat","description":"5mm thick eco-friendly yoga mat with anti-slip texture and alignment guides.","price":Decimal("89.00"),"category":"Sports","sku":"SPRT-001","image_url":"/products/sports-yoga.jpg","stock_quantity":85,"status":"available"},
                {"name":"Wireless Charging Pad Set","description":"Triple wireless charging station for phone, watch and earbuds.","price":Decimal("159.50"),"category":"Electronics","sku":"ELEC-003","image_url":"/products/electronics-charging.jpg","stock_quantity":40,"status":"available"},
                {"name":"Luxury Scented Candle Trio","description":"Hand-poured soy wax candles in amber glass vessels.","price":Decimal("78.00"),"category":"Home","sku":"HOME-001","image_url":"https://images.unsplash.com/photo-1602874801007-b2b4e8a8d8f2?w=600&q=80","stock_quantity":70,"status":"available"},
                {"name":"Designer Sunglasses","description":"Polarized designer sunglasses with titanium frames and gradient amber lenses.","price":Decimal("220.00"),"category":"Fashion","sku":"FASH-004","image_url":"https://images.unsplash.com/photo-1517841905240-472988babdf9?w=600&q=80","stock_quantity":25,"status":"available"},
                {"name":"Organic Lip Tint Collection","description":"Set of 5 moisturizing lip tints with natural pigments. Vegan and cruelty-free.","price":Decimal("55.00"),"category":"Cosmetics","sku":"COSM-003","image_url":"/products/cosmetics-lip.jpg","stock_quantity":95,"status":"available"},
            ]
            for p in products:
                db.add(Product(**p))
            db.commit()
            print(f"Seeded {len(products)} luxury products.")
        except Exception as exc:
            print(f"Seeding skipped (DB not ready): {exc}")
            db.rollback()
        finally:
            db.close()
    except Exception as exc:
        print(f"Seeding failed: {exc}")

if __name__ == "__main__":
    seed()

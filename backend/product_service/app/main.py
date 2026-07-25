import os
import logging
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
import uuid

from backend.shared.database import get_db, SessionLocal
from backend.shared.events import EventType, BaseEvent
from app.models import Product
from app.schemas import ProductCreate, ProductUpdate, ProductResponse, ProductSearchResponse
from decimal import Decimal
import uuid

def seed_demo_data():
    try:
        db = SessionLocal()
        try:
            if db.query(Product).first():
                return
            demo_products = [
                {"name":"Silk Evening Gown","description":"Luxurious midnight silk evening gown with delicate pearl embroidery. Hand-tailored for formal occasions.","price":Decimal("389.00"),"category":"Fashion","sku":"FASH-001","image_url":"/products/fashion-gown.jpg","stock_quantity":12,"status":"available"},
                {"name":"Wireless Noise-Canceling Headphones","description":"Premium over-ear headphones with 40-hour battery life, crystal-clear audio and adaptive noise cancellation.","price":Decimal("349.99"),"category":"Electronics","sku":"ELEC-001","image_url":"/products/electronics-headphones.jpg","stock_quantity":45,"status":"available"},
                {"name":"Organic Rose Serum","description":"Anti-aging facial serum with organic rose extract, hyaluronic acid and vitamin C. Dermatologist tested.","price":Decimal("89.50"),"category":"Cosmetics","sku":"COSM-001","image_url":"/products/cosmetics-serum.jpg","stock_quantity":120,"status":"available"},
                {"name":"Artisan Leather Tote","description":"Handcrafted Italian full-grain leather tote bag with brass hardware and suede lining. Timeless design.","price":Decimal("425.00"),"category":"Fashion","sku":"FASH-002","image_url":"/products/fashion-tote.jpg","stock_quantity":8,"status":"available"},
                {"name":"Smart Mirror Pro","description":"Interactive smart mirror with fitness tracking, weather display, and AI-powered skin analysis.","price":Decimal("599.00"),"category":"Electronics","sku":"ELEC-002","image_url":"/products/electronics-mirror.jpg","stock_quantity":15,"status":"available"},
                {"name":"Luxury Bath Gift Set","description":"Curated spa gift set with lavender bath salts, eucalyptus body scrub, silk eye mask and aromatherapy candle.","price":Decimal("129.99"),"category":"Cosmetics","sku":"COSM-002","image_url":"/products/cosmetics-bath.jpg","stock_quantity":60,"status":"available"},
                {"name":"Minimalist Silk Scarf","description":"Hand-painted 100% mulberry silk scarf with geometric patterns. Measures 90x90cm.","price":Decimal("145.00"),"category":"Fashion","sku":"FASH-003","image_url":"/products/fashion-scarf.jpg","stock_quantity":30,"status":"available"},
                {"name":"Premium Yoga Mat","description":"5mm thick eco-friendly yoga mat with anti-slip texture, alignment guides and carrying strap included.","price":Decimal("89.00"),"category":"Sports","sku":"SPRT-001","image_url":"/products/sports-yoga.jpg","stock_quantity":85,"status":"available"},
                {"name":"Wireless Charging Pad Set","description":"Triple wireless charging station for phone, watch and earbuds. Sleek aluminum and glass finish.","price":Decimal("159.50"),"category":"Electronics","sku":"ELEC-003","image_url":"/products/electronics-charging.jpg","stock_quantity":40,"status":"available"},
                {"name":"Luxury Scented Candle Trio","description":"Hand-poured soy wax candles in amber glass vessels. Scents: Sandalwood, White Tea, and Cedarwood.","price":Decimal("78.00"),"category":"Home","sku":"HOME-001","image_url":"https://images.unsplash.com/photo-1602874801007-b2b4e8a8d8f2?w=600&q=80","stock_quantity":70,"status":"available"},
                {"name":"Designer Sunglasses","description":"Polarized designer sunglasses with titanium frames and gradient amber lenses. UV400 protection.","price":Decimal("220.00"),"category":"Fashion","sku":"FASH-004","image_url":"https://images.unsplash.com/photo-1517841905240-472988babdf9?w=600&q=80","stock_quantity":25,"status":"available"},
                {"name":"Organic Lip Tint Collection","description":"Set of 5 moisturizing lip tints with natural pigments. Vegan and cruelty-free formulation.","price":Decimal("55.00"),"category":"Cosmetics","sku":"COSM-003","image_url":"/products/cosmetics-lip.jpg","stock_quantity":95,"status":"available"},
            ]
            for d in demo_products:
                db.add(Product(**d))
            db.commit()
            logger.info("Seeded 12 luxury products.")
        except Exception as exc:
            logger.warning(f"Seeding skipped (DB not ready): {exc}")
            db.rollback()
        finally:
            db.close()
    except Exception as exc:
        logger.warning(f"Seeding failed: {exc}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Seed demo data on startup
seed_demo_data()

app = FastAPI(title="Product Service", version="1.0.0", docs_url="/docs")

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy", "service": "product-service"}

@app.get("/products", response_model=ProductSearchResponse, tags=["products"])
def list_products(
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%")
            )
        )
    total = query.count()
    results = query.offset((page - 1) * limit).limit(limit).all()
    return ProductSearchResponse(results=results, total=total, page=page, limit=limit)

@app.get("/products/{product_id}", response_model=ProductResponse, tags=["products"])
def get_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/products", response_model=ProductResponse, status_code=201, tags=["products"])
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.sku == product.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    logger.info(f"Product created: {db_product.id}")
    return db_product

@app.put("/products/{product_id}", response_model=ProductResponse, tags=["products"])
def update_product(product_id: uuid.UUID, update: ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(db_product, field, value)
    db.commit()
    db.refresh(db_product)
    logger.info(f"Product updated: {db_product.id}")
    return db_product

@app.delete("/products/{product_id}", status_code=204, tags=["products"])
def delete_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db_product.status = "discontinued"
    db.commit()
    logger.info(f"Product discontinued: {db_product.id}")
    return None

@app.get("/categories", tags=["products"])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Product.category).distinct().all()
    return {"categories": [c[0] for c in categories if c[0]]}

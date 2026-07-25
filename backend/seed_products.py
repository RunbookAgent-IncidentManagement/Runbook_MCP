#!/usr/bin/env python
"""Seed demo products into the database."""
import os
import sys
sys.path.insert(0, "/app")
os.environ["PYTHONPATH"] = "/app"

from backend.shared.database import SessionLocal
# Try common import paths based on PYTHONPATH
try:
    from app.models import Product
except ImportError:
    from product_service.app.models import Product
from sqlalchemy.orm import Session
from decimal import Decimal
import uuid

def seed():
    db = SessionLocal()
    try:
        if db.query(Product).first():
            print("Database already has data. Skipping seed.")
            return
        products = [
            Product(
                id=uuid.UUID("a1111111-1111-1111-1111-111111111111"),
                name="Resilient Router",
                description="Enterprise-grade network hardware with automated recovery and self-healing capabilities.",
                price=Decimal("299.99"),
                category="Networking",
                sku="SKU-001",
                stock_quantity=50,
                status="available"
            ),
            Product(
                id=uuid.UUID("a2222222-2222-2222-2222-222222222222"),
                name="Cloud Storage Array",
                description="Scalable object storage for event-driven applications with multi-region replication.",
                price=Decimal("149.50"),
                category="Storage",
                sku="SKU-002",
                stock_quantity=200,
                status="available"
            ),
            Product(
                id=uuid.UUID("a3333333-3333-3333-3333-333333333333"),
                name="Monitoring Dashboard",
                description="Real-time observability with AI-driven alerting and automated incident correlation.",
                price=Decimal("499.00"),
                category="Observability",
                sku="SKU-003",
                stock_quantity=25,
                status="available"
            ),
            Product(
                id=uuid.UUID("a4444444-4444-4444-4444-444444444444"),
                name="K8s Operator Kit",
                description="Pre-configured Kubernetes controllers, CRDs, and deployment templates for resilient services.",
                price=Decimal("199.99"),
                category="DevOps",
                sku="SKU-004",
                stock_quantity=100,
                status="available"
            ),
        ]
        for p in products:
            db.add(p)
        db.commit()
        print(f"Seeded {len(products)} demo products successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()

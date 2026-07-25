from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ecommerce")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Ensure tables exist on startup (resilient for Docker Compose resets)
# Import each service's models individually so one missing module doesn't block others
try:
    from backend.product_service.app import models as product_models
except Exception:
    product_models = None
try:
    from backend.cart_service.app import models as cart_models
except Exception:
    cart_models = None
try:
    from backend.order_service.app import models as order_models
except Exception:
    order_models = None
try:
    from backend.payment_service.app import models as payment_models
except Exception:
    payment_models = None
try:
    from backend.notification_service.app import models as notification_models
except Exception:
    notification_models = None

# Always attempt to create all registered tables (handles reset volumes / fresh DBs)
try:
    Base.metadata.create_all(bind=engine)
except Exception as exc:
    import logging
    logging.getLogger(__name__).warning(f"Base.metadata.create_all skipped (DB may not be ready yet): {exc}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

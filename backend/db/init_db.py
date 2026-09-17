import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.db.session import engine, Base, SessionLocal
from backend.models import (
    Role, User, Product, UploadJob, ValidationResult,
    SalesTransaction, DailyProductDemand, ForecastRun,
    ForecastItem, ForecastEvaluation, InventoryState,
    InventoryRecommendation, AnomalyAlert, ChatSession,
    ChatMessage, AuditLog, MarketPriceObservation, ProductCommodityMapping
)
from backend.core.security import get_password_hash

def init_db():
    print("Connecting to database and creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

    db = SessionLocal()
    try:
        # Seed Roles
        roles_data = [
            {"id": 1, "name": "admin", "description": "System Administrator with full management access"},
            {"id": 2, "name": "manager", "description": "Store and Inventory Manager with operational access"},
            {"id": 3, "name": "viewer", "description": "Read-only analyst viewer"},
        ]
        for r_info in roles_data:
            role = db.query(Role).filter(Role.name == r_info["name"]).first()
            if not role:
                role = Role(**r_info)
                db.add(role)
        db.commit()
        print("Roles seeded.")

        # Seed Default Admin User
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                email="admin@demandintelligence.com",
                username="admin",
                hashed_password=get_password_hash("Admin@123"),
                full_name="System Administrator",
                role_id=1,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("Default admin created: admin / Admin@123")
        else:
            print("Admin user already exists.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    init_db()

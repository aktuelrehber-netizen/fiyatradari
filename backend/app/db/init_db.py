"""
Initial database setup script
Creates default admin user and initial settings
"""
import sys
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, engine
from app.db.base import Base
from app.db import models
from app.core.security import get_password_hash


def init_db():
    """Initialize database with default data"""
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if admin user exists
        admin = db.query(models.User).filter(models.User.username == "admin").first()
        
        if not admin:
            print("Creating default admin user...")
            admin = models.User(
                email="admin@firsatradari.com",
                username="admin",
                full_name="Admin User",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_admin=True
            )
            db.add(admin)
            db.commit()
            print("✓ Default admin user created")
            print("  Username: admin")
            print("  Password: admin123")
            print("  IMPORTANT: Change this password immediately!")
        else:
            print("✓ Admin user already exists")
        
        # Create default system settings
        default_settings = [
            {
                "key": "amazon_access_key",
                "value": "",
                "data_type": "string",
                "description": "Amazon PA API Access Key",
                "group": "amazon"
            },
            {
                "key": "amazon_secret_key",
                "value": "",
                "data_type": "string",
                "description": "Amazon PA API Secret Key",
                "group": "amazon"
            },
            {
                "key": "amazon_partner_tag",
                "value": "",
                "data_type": "string",
                "description": "Amazon Partner Tag",
                "group": "amazon"
            },
            {
                "key": "telegram_bot_token",
                "value": "",
                "data_type": "string",
                "description": "Telegram Bot Token",
                "group": "telegram"
            },
            {
                "key": "telegram_channel_id",
                "value": "",
                "data_type": "string",
                "description": "Telegram Channel ID",
                "group": "telegram"
            },
            {
                "key": "deal_threshold_percentage",
                "value": "15",
                "data_type": "int",
                "description": "Minimum discount percentage to create a deal",
                "group": "worker"
            },
            {
                "key": "price_check_interval_hours",
                "value": "6",
                "data_type": "int",
                "description": "Hours between price checks",
                "group": "worker"
            },
            {
                "key": "max_products_per_category",
                "value": "100",
                "data_type": "int",
                "description": "Maximum products to track per category",
                "group": "worker"
            }
        ]
        
        for setting_data in default_settings:
            existing = db.query(models.SystemSetting).filter(
                models.SystemSetting.key == setting_data["key"]
            ).first()
            
            if not existing:
                setting = models.SystemSetting(**setting_data)
                db.add(setting)
        
        db.commit()
        print("✓ Default settings created")
        
        # Create sample category
        sample_category = db.query(models.Category).filter(
            models.Category.slug == "elektronik"
        ).first()
        
        if not sample_category:
            print("Creating sample category...")
            sample_category = models.Category(
                name="Elektronik",
                slug="elektronik",
                description="Elektronik ürünler",
                amazon_browse_node_ids=[],
                is_active=True,
                selection_rules={
                    "min_price": 100,
                    "max_price": 10000,
                    "min_rating": 4.0,
                    "min_review_count": 50
                },
                check_interval_hours=6,
                max_products=100
            )
            db.add(sample_category)
            db.commit()
            print("✓ Sample category created")
        
        print("\n✅ Database initialization completed successfully!")
        print("\nNext steps:")
        print("1. Login to admin panel with admin/admin123")
        print("2. Change the admin password")
        print("3. Configure Amazon API settings")
        print("4. Configure Telegram settings")
        print("5. Add categories and start tracking products")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Initializing Fiyat Radarı database...")
    init_db()

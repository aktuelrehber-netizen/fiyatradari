#!/usr/bin/env python3
"""
Create admin user for Fiyatradari
Usage: python create_admin.py
"""

import sys
from app.db.database import SessionLocal
from app.db.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin(username: str = "admin", email: str = "admin@firsatradari.com", password: str = "Admin123!"):
    """Create admin user"""
    db = SessionLocal()
    
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"❌ User '{username}' already exists!")
            return False
        
        # Create admin user
        admin_user = User(
            username=username,
            email=email,
            hashed_password=pwd_context.hash(password),
            is_active=True,
            is_superuser=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ Admin user created successfully!")
        print(f"   Username: {admin_user.username}")
        print(f"   Email: {admin_user.email}")
        print(f"   Password: {password}")
        print(f"   ID: {admin_user.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Creating admin user for Fiyatradari...")
    
    # Custom credentials
    username = input("Username (default: admin): ").strip() or "admin"
    email = input("Email (default: admin@firsatradari.com): ").strip() or "admin@firsatradari.com"
    password = input("Password (default: Admin123!): ").strip() or "Admin123!"
    
    create_admin(username, email, password)

#!/usr/bin/env python3
"""
Seed OpenAI API settings
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db import models

def seed_openai_settings():
    """Create default OpenAI API settings"""
    db = SessionLocal()
    
    try:
        # OpenAI settings to create
        openai_settings = [
            {
                "key": "openai_api_key",
                "value": "",
                "description": "OpenAI API Key (sk-...)",
                "group": "openai",
                "data_type": "string",
                "is_secret": True
            },
            {
                "key": "openai_model",
                "value": "gpt-3.5-turbo",
                "description": "Kullanılacak OpenAI modeli (gpt-4, gpt-3.5-turbo, gpt-4-turbo)",
                "group": "openai",
                "data_type": "string",
                "is_secret": False
            },
            {
                "key": "openai_max_tokens",
                "value": "1000",
                "description": "Maksimum token sayısı (istek başına)",
                "group": "openai",
                "data_type": "integer",
                "is_secret": False
            },
            {
                "key": "openai_temperature",
                "value": "0.7",
                "description": "Model yaratıcılığı (0.0-2.0, düşük=tutarlı, yüksek=yaratıcı)",
                "group": "openai",
                "data_type": "float",
                "is_secret": False
            },
            {
                "key": "openai_enabled",
                "value": "false",
                "description": "OpenAI entegrasyonu aktif mi? (true/false)",
                "group": "openai",
                "data_type": "boolean",
                "is_secret": False
            }
        ]
        
        created_count = 0
        skipped_count = 0
        
        for setting_data in openai_settings:
            # Check if setting already exists
            existing = db.query(models.Setting).filter(
                models.Setting.key == setting_data["key"]
            ).first()
            
            if existing:
                print(f"⏭️  Setting '{setting_data['key']}' already exists, skipping...")
                skipped_count += 1
                continue
            
            # Create new setting
            setting = models.Setting(**setting_data)
            db.add(setting)
            created_count += 1
            print(f"✅ Created setting: {setting_data['key']}")
        
        db.commit()
        
        print(f"\n{'='*50}")
        print(f"✨ OpenAI Settings Seed Completed!")
        print(f"{'='*50}")
        print(f"Created: {created_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Total:   {created_count + skipped_count}")
        
    except Exception as e:
        print(f"❌ Error seeding OpenAI settings: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Seeding OpenAI API Settings...\n")
    seed_openai_settings()

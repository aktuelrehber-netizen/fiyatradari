"""
Seed proxy settings to database
Run once to add proxy configuration options to system_settings table
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import get_db
from app.db.models import SystemSetting

def seed_proxy_settings():
    """Add proxy settings to database"""
    
    proxy_settings = [
        {
            'key': 'proxy.enabled',
            'value': 'false',
            'data_type': 'bool',
            'description': 'Proxy kullanımını aktif/pasif et (true/false)',
            'group': 'proxy',
            'is_secret': False
        },
        {
            'key': 'proxy.http_proxy',
            'value': '',
            'data_type': 'str',
            'description': 'Tek proxy (http://user:pass@proxy.com:8080)',
            'group': 'proxy',
            'is_secret': False
        },
        {
            'key': 'proxy.list',
            'value': '',
            'data_type': 'str',
            'description': 'Proxy listesi (virgülle ayrılmış: proxy1:8080,proxy2:8080)',
            'group': 'proxy',
            'is_secret': False
        },
        {
            'key': 'proxy.host',
            'value': '',
            'data_type': 'str',
            'description': 'Premium proxy host (örn: proxy.brightdata.com)',
            'group': 'proxy',
            'is_secret': False
        },
        {
            'key': 'proxy.port',
            'value': '',
            'data_type': 'str',
            'description': 'Premium proxy port (örn: 22225)',
            'group': 'proxy',
            'is_secret': False
        },
        {
            'key': 'proxy.user',
            'value': '',
            'data_type': 'str',
            'description': 'Premium proxy kullanıcı adı',
            'group': 'proxy',
            'is_secret': False
        },
        {
            'key': 'proxy.pass',
            'value': '',
            'data_type': 'str',
            'description': 'Premium proxy şifre',
            'group': 'proxy',
            'is_secret': True
        },
    ]
    
    with get_db() as db:
        for setting_data in proxy_settings:
            # Check if setting exists
            existing = db.query(SystemSetting).filter(
                SystemSetting.key == setting_data['key']
            ).first()
            
            if existing:
                print(f"⚠️  Setting already exists: {setting_data['key']}")
                continue
            
            # Create new setting
            setting = SystemSetting(
                key=setting_data['key'],
                value=setting_data['value'],
                data_type=setting_data['data_type'],
                description=setting_data['description'],
                group=setting_data['group'],
                is_secret=setting_data.get('is_secret', False)
            )
            
            db.add(setting)
            print(f"✅ Added setting: {setting_data['key']}")
        
        db.commit()
        print("\n✅ Proxy settings seeded successfully!")


if __name__ == '__main__':
    seed_proxy_settings()

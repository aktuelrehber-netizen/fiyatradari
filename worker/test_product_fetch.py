"""
Test script for product fetching system
Run: python3 test_product_fetch.py
"""
from datetime import datetime
from decimal import Decimal

from database import get_db, Category, Product
from services.amazon_client import AmazonPAAPIClient
from celery_tasks import fetch_category_products

def test_pa_api_connection():
    """Test Amazon PA-API connection"""
    print("\n" + "="*60)
    print("🔍 TEST 1: Amazon PA-API Connection")
    print("="*60)
    
    try:
        client = AmazonPAAPIClient()
        
        if not client.enabled:
            print("❌ PA-API not enabled!")
            print("   Check: AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_PARTNER_TAG")
            return False
        
        print("✅ PA-API client initialized successfully")
        print(f"   Region: {client.api.region if hasattr(client, 'api') else 'N/A'}")
        print(f"   Marketplace: {client.api.marketplace if hasattr(client, 'api') else 'N/A'}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_category_setup():
    """Test if categories are properly configured"""
    print("\n" + "="*60)
    print("🔍 TEST 2: Category Configuration")
    print("="*60)
    
    try:
        with get_db() as db:
            categories = db.query(Category).filter(Category.is_active == True).all()
            
            if not categories:
                print("❌ No active categories found!")
                print("   Create a category first in admin panel")
                return False
            
            print(f"✅ Found {len(categories)} active categories:\n")
            
            valid_categories = []
            for cat in categories:
                browse_nodes = cat.amazon_browse_node_ids or []
                max_products = cat.max_products or 100
                
                print(f"📦 {cat.name} (ID: {cat.id})")
                print(f"   Browse Nodes: {len(browse_nodes)}")
                
                if browse_nodes:
                    print(f"   Nodes: {browse_nodes[:2]}{'...' if len(browse_nodes) > 2 else ''}")
                    print(f"   Max Products: {max_products}")
                    print(f"   Selection Rules: {'✅' if cat.selection_rules else '❌'}")
                    valid_categories.append(cat)
                else:
                    print(f"   ⚠️  No browse nodes configured!")
                
                print()
            
            return valid_categories
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_browse_node_search(category):
    """Test searching products from a browse node"""
    print("\n" + "="*60)
    print(f"🔍 TEST 3: Browse Node Search - {category.name}")
    print("="*60)
    
    try:
        client = AmazonPAAPIClient()
        browse_node = category.amazon_browse_node_ids[0]
        
        print(f"📡 Fetching from browse node: {browse_node}")
        print(f"   Page: 1")
        print(f"   Items per page: 10")
        print(f"   Original selection rules: {category.selection_rules or 'None'}")
        
        # Test with relaxed rules (remove rating to see if API filtering works)
        test_rules = None
        if category.selection_rules:
            test_rules = category.selection_rules.copy()
            # Remove rating filter to test
            if 'min_rating' in test_rules:
                removed_rating = test_rules.pop('min_rating')
                print(f"   ⚠️  Removed min_rating: {removed_rating} for testing")
            if 'max_rating' in test_rules:
                test_rules.pop('max_rating')
        
        print(f"   Test rules (API filtering): {test_rules or 'None'}")
        print()
        
        items = client.search_items_by_browse_node(
            browse_node_id=browse_node,
            page=1,
            items_per_page=10,
            selection_rules=test_rules  # Use relaxed rules
        )
        
        if not items:
            print("⚠️  No items found!")
            print("   Reasons:")
            print("   - Browse node ID might be incorrect")
            print("   - Selection rules too strict")
            print("   - PA-API credentials issue")
            return False
        
        print(f"✅ Found {len(items)} items!\n")
        
        for i, item in enumerate(items[:3], 1):
            print(f"{i}. {item.get('title', 'N/A')[:60]}")
            print(f"   ASIN: {item.get('asin')}")
            print(f"   Price: {item.get('current_price')} {item.get('currency', 'TRY')}")
            print(f"   Rating: {item.get('rating')} ({item.get('review_count')} reviews)")
            print(f"   Available: {item.get('is_available')}")
            print()
        
        return items
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def test_product_insertion(category, items):
    """Test inserting products to database"""
    print("\n" + "="*60)
    print("🔍 TEST 4: Product Database Insertion")
    print("="*60)
    
    try:
        with get_db() as db:
            created = 0
            updated = 0
            
            for item in items[:3]:  # Only test first 3
                asin = item.get('asin')
                if not asin:
                    continue
                
                product = db.query(Product).filter(Product.asin == asin).first()
                
                if product:
                    product.current_price = item.get('current_price')
                    product.is_available = item.get('is_available', True)
                    product.last_checked_at = datetime.utcnow()
                    updated += 1
                    print(f"📝 Updated: {asin} - {product.title[:40]}")
                else:
                    product = Product(
                        asin=asin,
                        title=item.get('title', '')[:500],
                        brand=item.get('brand'),
                        current_price=Decimal(str(item['current_price'])) if item.get('current_price') else None,
                        currency=item.get('currency', 'TRY'),
                        image_url=item.get('image_url'),
                        rating=item.get('rating'),
                        review_count=item.get('review_count'),
                        is_available=item.get('is_available', True),
                        category_id=category.id,
                        amazon_data=item,
                        last_checked_at=datetime.utcnow()
                    )
                    db.add(product)
                    created += 1
                    print(f"✨ Created: {asin} - {item.get('title', '')[:40]}")
            
            db.commit()
            
            print(f"\n✅ Database operations complete!")
            print(f"   Created: {created}")
            print(f"   Updated: {updated}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def test_celery_task(category):
    """Test Celery task dispatch"""
    print("\n" + "="*60)
    print("🔍 TEST 5: Celery Task Dispatch")
    print("="*60)
    
    try:
        browse_node = category.amazon_browse_node_ids[0]
        
        print(f"📤 Dispatching task...")
        print(f"   Category: {category.name} (ID: {category.id})")
        print(f"   Browse Node: {browse_node}")
        print(f"   Page: 1")
        print()
        
        result = fetch_category_products.apply_async(
            args=[category.id, browse_node, 1],
            priority=8
        )
        
        print(f"✅ Task dispatched successfully!")
        print(f"   Task ID: {result.id}")
        print(f"   State: {result.state}")
        print()
        print("🔍 Waiting for result (max 30 seconds)...")
        
        try:
            task_result = result.get(timeout=30)
            print(f"\n✅ Task completed!")
            print(f"   Status: {task_result.get('status')}")
            print(f"   Created: {task_result.get('items_created', 0)}")
            print(f"   Updated: {task_result.get('items_updated', 0)}")
            return True
        except Exception as timeout_error:
            print(f"⚠️  Task timeout or error: {timeout_error}")
            print(f"   Task might still be running in background")
            print(f"   Check: docker compose logs celery_worker -f")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def main():
    """Run all tests"""
    print("\n")
    print("="*60)
    print("🧪 PRODUCT FETCH SYSTEM TEST SUITE")
    print("="*60)
    
    # Test 1: PA-API Connection
    if not test_pa_api_connection():
        print("\n⛔ PA-API connection failed. Fix credentials first!")
        return
    
    # Test 2: Category Setup
    categories = test_category_setup()
    if not categories:
        print("\n⛔ No valid categories found. Create categories first!")
        return
    
    # Pick first valid category
    category = categories[0]
    
    # Test 3: Browse Node Search
    items = test_browse_node_search(category)
    if not items:
        print("\n⛔ Browse node search failed. Check browse node ID!")
        return
    
    # Test 4: Product Insertion
    if not test_product_insertion(category, items):
        print("\n⛔ Database insertion failed!")
        return
    
    # Test 5: Celery Task
    test_celery_task(category)
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETE!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Check admin panel: http://your-domain.com/admin/products")
    print("2. Test manual fetch: Click Download icon on category")
    print("3. Monitor logs: docker compose logs celery_worker -f")
    print()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test Amazon Product Advertising API
Direct test without worker dependencies
"""

try:
    from amazon_paapi import AmazonApi
    print("✅ amazon-paapi library loaded")
except ImportError:
    print("❌ amazon-paapi not installed. Installing...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'amazon-paapi'])
    from amazon_paapi import AmazonApi

# Credentials (NEW - Generated Nov 16, 2025 - Second Attempt)
ACCESS_KEY = "AKPAOXHNPR1763279592"
SECRET_KEY = "QumEXcpIkotRGAPKy+K2AOI17v65NLz2NqaWOYd3"
PARTNER_TAG = "firsatradar06-21"
COUNTRY = "TR"

print("\n" + "="*80)
print("🧪 TESTING AMAZON PA API")
print("="*80)
print(f"Access Key: {ACCESS_KEY}")
print(f"Partner Tag: {PARTNER_TAG}")
print(f"Country: {COUNTRY}")
print(f"Marketplace: amazon.com.tr")
print("="*80 + "\n")

try:
    # Initialize API
    print("🔄 Initializing Amazon API client...")
    amazon = AmazonApi(
        key=ACCESS_KEY,
        secret=SECRET_KEY,
        tag=PARTNER_TAG,
        country=COUNTRY
    )
    print("✅ API client initialized\n")
    
    # Test 1: Search by Browse Node (Kahve Makinesi)
    print("="*80)
    print("TEST 1: Search by Browse Node")
    print("="*80)
    browse_node = "12407999031"  # Kahve Makinesi
    print(f"Browse Node ID: {browse_node}")
    print(f"Searching for products...")
    
    result = amazon.search_items(
        browse_node_id=browse_node,
        item_count=5,
        item_page=1
    )
    
    if result and hasattr(result, 'items') and result.items:
        print(f"✅ SUCCESS! Found {len(result.items)} products\n")
        
        for idx, item in enumerate(result.items, 1):
            print(f"\n📦 Product {idx}:")
            print(f"   ASIN: {item.asin}")
            
            # Title
            if hasattr(item, 'item_info') and item.item_info:
                if hasattr(item.item_info, 'title') and item.item_info.title:
                    print(f"   Title: {item.item_info.title.display_value}")
            
            # Price
            if hasattr(item, 'offers') and item.offers:
                if hasattr(item.offers, 'listings') and item.offers.listings:
                    listing = item.offers.listings[0]
                    if hasattr(listing, 'price') and listing.price:
                        price = listing.price
                        print(f"   Price: {price.amount} {price.currency}")
            
            # URL
            if hasattr(item, 'detail_page_url'):
                print(f"   URL: {item.detail_page_url}")
    else:
        print("⚠️  No items found in response")
        print(f"Response: {result}")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETED SUCCESSFULLY!")
    print("="*80)
    
except Exception as e:
    print("\n" + "="*80)
    print("❌ ERROR!")
    print("="*80)
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {str(e)}")
    
    # Check if it's an API exception
    if hasattr(e, '__dict__'):
        print("\nError Details:")
        for key, value in e.__dict__.items():
            print(f"  {key}: {value}")
    
    print("\n" + "="*80)
    
    import traceback
    print("\nFull Traceback:")
    print(traceback.format_exc())

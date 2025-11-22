#!/usr/bin/env python3
"""
Manual task dispatcher for testing
Usage: python3 manual_tasks.py
"""
import sys
from celery_tasks import (
    check_product_price,
    batch_price_check,
    continuous_queue_refill,
    schedule_product_fetch,
    fetch_category_products
)
from database import get_db, Product, Category

def check_single_product():
    """Check price for a single product"""
    with get_db() as db:
        product = db.query(Product).filter(Product.is_active == True).first()
        if product:
            print(f"📦 Checking product: {product.id} - {product.title[:50]}")
            result = check_product_price.apply_async(
                args=[product.id],
                priority=10
            )
            print(f"✅ Task dispatched: {result.id}")
        else:
            print("❌ No active products found")

def refill_queue():
    """Refill the price check queue"""
    print("🔄 Refilling queue...")
    result = continuous_queue_refill.apply_async(priority=10)
    print(f"✅ Task dispatched: {result.id}")

def fetch_products():
    """Fetch new products from Amazon (ALL categories)"""
    print("📥 Scheduling product fetch for ALL categories...")
    result = schedule_product_fetch.apply_async(priority=10)
    print(f"✅ Task dispatched: {result.id}")
    print("📊 This will fetch products for all active categories from Amazon")

def fetch_single_category():
    """Fetch products for a single category"""
    with get_db() as db:
        category = db.query(Category).filter(Category.is_active == True).first()
        if category and category.amazon_browse_node_ids:
            browse_node = category.amazon_browse_node_ids[0]
            print(f"📥 Fetching products for category: {category.name}")
            print(f"   Browse node: {browse_node}")
            result = fetch_category_products.apply_async(
                args=[category.id, browse_node, 1],
                priority=10
            )
            print(f"✅ Task dispatched: {result.id}")
        else:
            print("❌ No active category with browse nodes found")

def check_multiple_products(limit=10):
    """Check price for multiple products"""
    with get_db() as db:
        products = db.query(Product).filter(Product.is_active == True).limit(limit).all()
        product_ids = [p.id for p in products]
        
        if product_ids:
            print(f"📦 Checking {len(product_ids)} products")
            result = batch_price_check.apply_async(
                args=[product_ids],
                priority=10
            )
            print(f"✅ Task dispatched: {result.id}")
        else:
            print("❌ No active products found")

if __name__ == "__main__":
    print("\n🎯 Manual Task Dispatcher\n")
    print("1. Check single product price")
    print("2. Refill price check queue")
    print("3. Fetch new products from Amazon (ALL categories) 🌙")
    print("4. Fetch single category products")
    print("5. Check multiple products (10)")
    print("0. Exit\n")
    
    choice = input("Select option: ").strip()
    print()
    
    if choice == "1":
        check_single_product()
    elif choice == "2":
        refill_queue()
    elif choice == "3":
        fetch_products()
    elif choice == "4":
        fetch_single_category()
    elif choice == "5":
        check_multiple_products(10)
    elif choice == "0":
        print("👋 Bye!")
    else:
        print("❌ Invalid option")

#!/usr/bin/env python3
"""
Test Proxy Configuration
Checks if proxies are loaded and working
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.proxy_manager import get_proxy_manager
from loguru import logger
import httpx
import asyncio

def test_proxy_config():
    """Test proxy configuration"""
    logger.info("=" * 60)
    logger.info("PROXY CONFIGURATION TEST")
    logger.info("=" * 60)
    
    # Get proxy manager
    proxy_manager = get_proxy_manager()
    
    if not proxy_manager:
        logger.error("❌ Proxy manager not initialized!")
        return False
    
    # Get stats
    stats = proxy_manager.get_stats()
    logger.info(f"📊 Proxy Stats:")
    logger.info(f"   Total proxies: {stats['total']}")
    logger.info(f"   Available: {stats['available']}")
    logger.info(f"   Failed: {stats['failed']}")
    
    if stats['total'] == 0:
        logger.warning("⚠️  No proxies configured!")
        logger.info("💡 Configure proxies in Admin Panel → Settings → Proxy Settings")
        return False
    
    # Get a proxy
    proxy = proxy_manager.get_proxy()
    if proxy:
        logger.success(f"✅ Got proxy: {proxy}")
        return True
    else:
        logger.error("❌ Failed to get proxy!")
        return False

async def test_proxy_request():
    """Test actual HTTP request with proxy"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING ACTUAL REQUEST WITH PROXY")
    logger.info("=" * 60)
    
    proxy_manager = get_proxy_manager()
    if not proxy_manager:
        logger.error("❌ Proxy manager not available")
        return False
    
    proxy = proxy_manager.get_proxy()
    if not proxy:
        logger.error("❌ No proxy available")
        return False
    
    # Test IP check endpoint
    test_urls = [
        "https://api.ipify.org?format=json",  # Returns your IP
        "https://httpbin.org/ip",              # Returns your IP
    ]
    
    for url in test_urls:
        try:
            logger.info(f"\n🧪 Testing: {url}")
            
            # Request WITH proxy
            logger.info(f"   Using proxy: {proxy}")
            async with httpx.AsyncClient(proxies=proxy, timeout=10.0) as client:
                response = await client.get(url)
                logger.success(f"   ✅ Response: {response.text.strip()}")
                
                # Mark proxy as successful
                proxy_manager.mark_proxy_success(proxy)
                
            # Request WITHOUT proxy (for comparison)
            logger.info(f"   Direct connection (no proxy):")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                logger.info(f"   📍 Response: {response.text.strip()}")
                
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            proxy_manager.mark_proxy_failure(proxy)
    
    return False

def main():
    """Main test function"""
    # Test 1: Configuration
    config_ok = test_proxy_config()
    
    if not config_ok:
        logger.error("\n❌ PROXY CONFIGURATION FAILED!")
        sys.exit(1)
    
    # Test 2: Actual request
    logger.info("\n" + "=" * 60)
    request_ok = asyncio.run(test_proxy_request())
    
    # Final result
    logger.info("\n" + "=" * 60)
    if config_ok and request_ok:
        logger.success("✅ PROXY TEST PASSED!")
        logger.info("🎉 Proxies are working correctly!")
    else:
        logger.error("❌ PROXY TEST FAILED!")
        logger.info("💡 Check your proxy configuration in Admin Panel")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()

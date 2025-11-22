"""
Proxy Manager - Rotating proxy support for web crawling
Supports multiple proxy providers and automatic rotation
"""
import random
import time
from typing import Optional, List, Dict
from loguru import logger
import redis
import os
import httpx


class ProxyManager:
    """
    Manages rotating proxies for web scraping
    
    Features:
    - Multiple proxy provider support (free + paid)
    - Automatic rotation
    - Health checking
    - Redis-based proxy pool sharing across workers
    - Fallback to direct connection if no proxies available
    """
    
    def __init__(self):
        # Proxy sources
        self.proxies: List[Dict] = []
        self.current_index = 0
        
        # Redis for distributed proxy pool
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'redis'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=3,  # Separate DB for proxy management
                decode_responses=True,
                socket_connect_timeout=2
            )
            self.redis_client.ping()
            self.use_redis = True
            logger.info("✅ Redis proxy manager initialized")
        except Exception as e:
            logger.warning(f"⚠️  Redis unavailable, using local proxy list: {e}")
            self.use_redis = False
        
        # Load proxies from config
        self._load_proxies()
    
    def _load_proxies(self):
        """Load proxies from environment or config"""
        
        # Option 1: Single proxy from environment
        proxy_url = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
        if proxy_url:
            self.proxies.append({
                'url': proxy_url,
                'protocol': 'http',
                'failures': 0,
                'last_used': 0
            })
            logger.info(f"✅ Loaded 1 proxy from environment")
            return
        
        # Option 2: Proxy list from environment (comma-separated)
        proxy_list = os.getenv('PROXY_LIST', '')
        if proxy_list:
            for proxy_url in proxy_list.split(','):
                proxy_url = proxy_url.strip()
                if proxy_url:
                    self.proxies.append({
                        'url': proxy_url,
                        'protocol': 'http',
                        'failures': 0,
                        'last_used': 0
                    })
            logger.info(f"✅ Loaded {len(self.proxies)} proxies from PROXY_LIST")
            return
        
        # Option 3: Premium proxy service (örnek: Bright Data, Smartproxy)
        proxy_host = os.getenv('PROXY_HOST')
        proxy_port = os.getenv('PROXY_PORT')
        proxy_user = os.getenv('PROXY_USER')
        proxy_pass = os.getenv('PROXY_PASS')
        
        if all([proxy_host, proxy_port, proxy_user, proxy_pass]):
            proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
            self.proxies.append({
                'url': proxy_url,
                'protocol': 'http',
                'failures': 0,
                'last_used': 0
            })
            logger.info(f"✅ Loaded premium proxy: {proxy_host}:{proxy_port}")
            return
        
        # Option 4: Free proxy list (fallback - not recommended for production)
        self._load_free_proxies()
    
    def _load_free_proxies(self):
        """
        Load free proxies from public sources
        
        ⚠️ WARNING: Free proxies are unreliable and slow!
        Use only for testing or as last resort.
        """
        # Hardcoded free proxy list (you can replace with API call)
        free_proxies = [
            # Format: "protocol://ip:port"
            # Add your free proxies here if needed
        ]
        
        for proxy_url in free_proxies:
            self.proxies.append({
                'url': proxy_url,
                'protocol': 'http',
                'failures': 0,
                'last_used': 0
            })
        
        if self.proxies:
            logger.info(f"⚠️  Loaded {len(self.proxies)} free proxies (not recommended for production)")
        else:
            logger.warning("⚠️  No proxies configured - will use direct connection")
    
    def get_proxy(self) -> Optional[Dict[str, str]]:
        """
        Get next proxy in rotation
        
        Returns:
            Proxy dict for httpx: {"http://": "...", "https://": "..."}
            Or None to use direct connection
        """
        if not self.proxies:
            return None
        
        # Filter out failed proxies (more than 5 consecutive failures)
        available_proxies = [p for p in self.proxies if p['failures'] < 5]
        
        if not available_proxies:
            logger.warning("⚠️  All proxies failed, resetting failure counts")
            for p in self.proxies:
                p['failures'] = 0
            available_proxies = self.proxies
        
        # Round-robin selection
        proxy = available_proxies[self.current_index % len(available_proxies)]
        self.current_index += 1
        
        # Update last used time
        proxy['last_used'] = time.time()
        
        # Format for httpx
        proxy_url = proxy['url']
        return {
            'http://': proxy_url,
            'https://': proxy_url
        }
    
    def mark_proxy_failed(self, proxy: Dict[str, str]):
        """Mark a proxy as failed"""
        if not proxy:
            return
        
        proxy_url = proxy.get('http://') or proxy.get('https://')
        if not proxy_url:
            return
        
        # Find and mark proxy as failed
        for p in self.proxies:
            if p['url'] == proxy_url:
                p['failures'] += 1
                logger.warning(f"⚠️  Proxy failed: {proxy_url} (failures: {p['failures']})")
                break
    
    def mark_proxy_success(self, proxy: Dict[str, str]):
        """Mark a proxy as successful (reset failure count)"""
        if not proxy:
            return
        
        proxy_url = proxy.get('http://') or proxy.get('https://')
        if not proxy_url:
            return
        
        # Find and reset failure count
        for p in self.proxies:
            if p['url'] == proxy_url:
                p['failures'] = 0
                break
    
    async def test_proxy(self, proxy_url: str) -> bool:
        """
        Test if a proxy is working
        
        Args:
            proxy_url: Proxy URL to test
        
        Returns:
            True if proxy works, False otherwise
        """
        test_url = "https://www.amazon.com.tr"
        
        try:
            async with httpx.AsyncClient(
                proxies={'http://': proxy_url, 'https://': proxy_url},
                timeout=10.0,
                follow_redirects=True
            ) as client:
                response = await client.get(test_url)
                return response.status_code == 200
        except Exception as e:
            logger.debug(f"Proxy test failed for {proxy_url}: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get proxy pool statistics"""
        if not self.proxies:
            return {
                'total': 0,
                'available': 0,
                'failed': 0,
                'status': 'no_proxies'
            }
        
        available = len([p for p in self.proxies if p['failures'] < 5])
        failed = len([p for p in self.proxies if p['failures'] >= 5])
        
        return {
            'total': len(self.proxies),
            'available': available,
            'failed': failed,
            'status': 'healthy' if available > 0 else 'degraded'
        }


# Global proxy manager instance
_proxy_manager = None


def get_proxy_manager() -> ProxyManager:
    """Get or create global proxy manager instance"""
    global _proxy_manager
    if _proxy_manager is None:
        _proxy_manager = ProxyManager()
    return _proxy_manager

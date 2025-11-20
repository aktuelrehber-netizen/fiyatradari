#!/usr/bin/env python3
"""
Load Testing Script for Fiyatradari API
Tests performance with 1M+ products scenario
"""

import asyncio
import aiohttp
import time
from typing import List, Dict
import statistics
from datetime import datetime

# Test Configuration
API_BASE_URL = "http://localhost:8000"
NGINX_BASE_URL = "http://localhost:80"
CONCURRENT_REQUESTS = 100
TOTAL_REQUESTS = 1000

class LoadTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results: List[Dict] = []
        
    async def fetch(self, session: aiohttp.ClientSession, endpoint: str, name: str):
        """Single HTTP request with timing"""
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}{endpoint}") as response:
                await response.text()
                duration = time.time() - start_time
                return {
                    "endpoint": name,
                    "status": response.status,
                    "duration": duration,
                    "success": response.status == 200
                }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "endpoint": name,
                "status": 0,
                "duration": duration,
                "success": False,
                "error": str(e)
            }
    
    async def run_batch(self, session: aiohttp.ClientSession, batch_size: int):
        """Run a batch of concurrent requests"""
        endpoints = [
            ("/health", "Health Check"),
            ("/api/v1/products/?limit=20", "Products List (20)"),
            ("/api/v1/products/?limit=50", "Products List (50)"),
            ("/api/v1/products/?limit=100", "Products List (100)"),
            ("/api/v1/deals/?limit=20", "Deals List (20)"),
            ("/api/v1/deals/?limit=50", "Deals List (50)"),
            ("/api/v1/categories/", "Categories List"),
        ]
        
        tasks = []
        for i in range(batch_size):
            endpoint, name = endpoints[i % len(endpoints)]
            tasks.append(self.fetch(session, endpoint, name))
        
        results = await asyncio.gather(*tasks)
        self.results.extend(results)
        return results
    
    async def run_test(self, total_requests: int, concurrent: int):
        """Run complete load test"""
        print(f"\n{'='*60}")
        print(f"🚀 LOAD TEST: {self.base_url}")
        print(f"{'='*60}")
        print(f"Total Requests: {total_requests}")
        print(f"Concurrent Requests: {concurrent}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            batches = total_requests // concurrent
            for i in range(batches):
                await self.run_batch(session, concurrent)
                if (i + 1) % 5 == 0:
                    print(f"Progress: {(i + 1) * concurrent}/{total_requests} requests completed...")
        
        total_duration = time.time() - start_time
        
        # Calculate statistics
        self.print_results(total_duration)
    
    def print_results(self, total_duration: float):
        """Print test results and statistics"""
        print(f"\n{'='*60}")
        print(f"📊 TEST RESULTS")
        print(f"{'='*60}\n")
        
        # Overall stats
        successful = sum(1 for r in self.results if r['success'])
        failed = len(self.results) - successful
        success_rate = (successful / len(self.results)) * 100
        
        print(f"Total Requests:    {len(self.results)}")
        print(f"Successful:        {successful} ({success_rate:.2f}%)")
        print(f"Failed:            {failed}")
        print(f"Total Duration:    {total_duration:.2f}s")
        print(f"Requests/Second:   {len(self.results) / total_duration:.2f}")
        
        # Response time stats
        durations = [r['duration'] for r in self.results if r['success']]
        if durations:
            print(f"\n⏱️  Response Time Statistics:")
            print(f"  Mean:      {statistics.mean(durations)*1000:.2f}ms")
            print(f"  Median:    {statistics.median(durations)*1000:.2f}ms")
            print(f"  Min:       {min(durations)*1000:.2f}ms")
            print(f"  Max:       {max(durations)*1000:.2f}ms")
            print(f"  Std Dev:   {statistics.stdev(durations)*1000:.2f}ms" if len(durations) > 1 else "  Std Dev:   N/A")
            
            # Percentiles
            sorted_durations = sorted(durations)
            p50 = sorted_durations[len(sorted_durations) // 2]
            p95 = sorted_durations[int(len(sorted_durations) * 0.95)]
            p99 = sorted_durations[int(len(sorted_durations) * 0.99)]
            
            print(f"\n📈 Percentiles:")
            print(f"  P50:       {p50*1000:.2f}ms")
            print(f"  P95:       {p95*1000:.2f}ms")
            print(f"  P99:       {p99*1000:.2f}ms")
        
        # Endpoint breakdown
        endpoint_stats = {}
        for result in self.results:
            endpoint = result['endpoint']
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {
                    'total': 0,
                    'success': 0,
                    'durations': []
                }
            endpoint_stats[endpoint]['total'] += 1
            if result['success']:
                endpoint_stats[endpoint]['success'] += 1
                endpoint_stats[endpoint]['durations'].append(result['duration'])
        
        print(f"\n🎯 Endpoint Performance:")
        for endpoint, stats in endpoint_stats.items():
            success_rate = (stats['success'] / stats['total']) * 100
            avg_duration = statistics.mean(stats['durations']) if stats['durations'] else 0
            print(f"  {endpoint}:")
            print(f"    Requests: {stats['total']} | Success: {success_rate:.1f}% | Avg: {avg_duration*1000:.2f}ms")
        
        print(f"\n{'='*60}\n")


async def main():
    """Main test execution"""
    print("\n" + "🔥"*30)
    print("FIYATRADARI LOAD TESTING")
    print("Performance Test for 1M+ Products")
    print("🔥"*30 + "\n")
    
    # Test 1: Direct API (no caching)
    print("Test 1: Direct Backend API (No Cache)")
    tester1 = LoadTester(API_BASE_URL)
    await tester1.run_test(TOTAL_REQUESTS, CONCURRENT_REQUESTS)
    
    await asyncio.sleep(2)
    
    # Test 2: Via Nginx with Rate Limiting
    print("\nTest 2: Via Nginx Proxy (With Rate Limiting)")
    tester2 = LoadTester(NGINX_BASE_URL)
    await tester2.run_test(TOTAL_REQUESTS, CONCURRENT_REQUESTS)
    
    # Comparison
    print("\n" + "="*60)
    print("🏆 COMPARISON: Direct API vs Nginx")
    print("="*60)
    
    api_avg = statistics.mean([r['duration'] for r in tester1.results if r['success']])
    nginx_avg = statistics.mean([r['duration'] for r in tester2.results if r['success']])
    
    print(f"Direct API Avg:    {api_avg*1000:.2f}ms")
    print(f"Nginx Proxy Avg:   {nginx_avg*1000:.2f}ms")
    
    if api_avg < nginx_avg:
        improvement = ((nginx_avg - api_avg) / nginx_avg) * 100
        print(f"Direct API is {improvement:.1f}% faster")
    else:
        improvement = ((api_avg - nginx_avg) / api_avg) * 100
        print(f"Nginx is {improvement:.1f}% faster")
    
    print("="*60 + "\n")
    
    print("✅ Load testing completed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during testing: {e}")

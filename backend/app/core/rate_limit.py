"""Rate limiting middleware for API security"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls  # Number of calls allowed
        self.period = period  # Time period in seconds
        self.cache: dict = defaultdict(list)
        self.cleanup_task = None
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Get current time
        now = datetime.now()
        
        # Clean old entries for this IP
        self.cache[client_ip] = [
            req_time for req_time in self.cache[client_ip]
            if now - req_time < timedelta(seconds=self.period)
        ]
        
        # Check rate limit
        if len(self.cache[client_ip]) >= self.calls:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Max {self.calls} requests per {self.period} seconds."
                },
                headers={
                    "Retry-After": str(self.period)
                }
            )
        
        # Add current request
        self.cache[client_ip].append(now)
        
        response = await call_next(request)
        return response


class LoginRateLimitMiddleware(BaseHTTPMiddleware):
    """Stricter rate limiting for login attempts"""
    
    def __init__(self, app, calls: int = 5, period: int = 300):  # 5 attempts per 5 minutes
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.cache: dict = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Only apply to login endpoint
        if request.url.path != "/api/v1/auth/login":
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        now = datetime.now()
        
        # Clean old entries
        self.cache[client_ip] = [
            req_time for req_time in self.cache[client_ip]
            if now - req_time < timedelta(seconds=self.period)
        ]
        
        # Check rate limit
        if len(self.cache[client_ip]) >= self.calls:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Too many login attempts. Try again in {self.period // 60} minutes."
                },
                headers={
                    "Retry-After": str(self.period)
                }
            )
        
        # Add current request
        self.cache[client_ip].append(now)
        
        response = await call_next(request)
        return response

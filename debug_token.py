#!/usr/bin/env python3
"""
Debug script to decode and validate JWT tokens from localStorage
"""
import sys
from jose import jwt, JWTError
from datetime import datetime

# Copy these from your .env file
SECRET_KEY = "your-super-secret-key-change-this-in-production"
ALGORITHM = "HS256"

def decode_token(token: str):
    """Decode and validate a JWT token"""
    try:
        print(f"Token (first 50 chars): {token[:50]}...")
        print(f"Token length: {len(token)}")
        print(f"\nDecoding with:")
        print(f"SECRET_KEY: {SECRET_KEY[:20]}...")
        print(f"ALGORITHM: {ALGORITHM}")
        print()
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        print("✅ Token decoded successfully!")
        print(f"\nPayload: {payload}")
        
        # Check expiration
        if 'exp' in payload:
            exp_timestamp = payload['exp']
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            now = datetime.utcnow()
            
            print(f"\nExpiration: {exp_datetime}")
            print(f"Current time: {now}")
            
            if exp_datetime < now:
                print("❌ Token is EXPIRED")
            else:
                print(f"✅ Token is valid for {exp_datetime - now}")
        
        # Check user_id
        if 'sub' in payload:
            print(f"\nUser ID (sub): {payload['sub']}")
        else:
            print("\n❌ No 'sub' field in token!")
            
    except JWTError as e:
        print(f"❌ JWT Decode Error: {e}")
        print("\nPossible causes:")
        print("1. Token was created with a different SECRET_KEY")
        print("2. Token is malformed")
        print("3. Token signature is invalid")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_token.py <YOUR_JWT_TOKEN>")
        print("\nOr run in browser console to get token:")
        print("  localStorage.getItem('token')")
        sys.exit(1)
    
    token = sys.argv[1]
    decode_token(token)

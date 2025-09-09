#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Token Debug and Access Token Generator
Author: AI Assistant (Debug token issues and generate fresh tokens)

This script helps debug token issues and generate fresh access tokens
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Load environment
from dotenv import load_dotenv, set_key
load_dotenv()

def check_token_storage():
    """🔍 Check how tokens are stored and loaded."""
    print("🔍 TOKEN STORAGE ANALYSIS")
    print("=" * 50)
    
    # Check .env file
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file exists")
        with open(env_file, 'r') as f:
            content = f.read()
            if 'KITE_ACCESS_TOKEN' in content:
                print("✅ KITE_ACCESS_TOKEN found in .env")
                for line in content.split('\n'):
                    if line.startswith('KITE_ACCESS_TOKEN'):
                        token_value = line.split('=', 1)[1].strip()
                        print(f"📋 Token in file: {token_value[:10]}...{token_value[-5:]} (length: {len(token_value)})")
            else:
                print("❌ KITE_ACCESS_TOKEN not found in .env")
    else:
        print("❌ .env file not found")
    
    # Check environment variables
    print("\n🌍 ENVIRONMENT VARIABLES:")
    api_key = os.getenv('KITE_API_KEY')
    access_token = os.getenv('KITE_ACCESS_TOKEN')
    api_secret = os.getenv('KITE_API_SECRET')
    
    print(f"KITE_API_KEY: {'✅ Set' if api_key else '❌ Missing'} ({len(api_key) if api_key else 0} chars)")
    print(f"KITE_ACCESS_TOKEN: {'✅ Set' if access_token else '❌ Missing'} ({len(access_token) if access_token else 0} chars)")
    print(f"KITE_API_SECRET: {'✅ Set' if api_secret else '❌ Missing'} ({len(api_secret) if api_secret else 0} chars)")
    
    if access_token:
        print(f"📋 Environment token: {access_token[:10]}...{access_token[-5:]}")
    
    # Check other token files
    print("\n📁 OTHER TOKEN STORAGE:")
    token_files = [
        'tokens/secure_tokens.json',
        'tokens.json',
        '.tokens',
        'kite_tokens.json'
    ]
    
    for token_file in token_files:
        if Path(token_file).exists():
            print(f"✅ Found: {token_file}")
            try:
                import json
                with open(token_file, 'r') as f:
                    data = json.load(f)
                    if 'access_token' in data:
                        stored_token = data['access_token']
                        print(f"   Token: {stored_token[:10]}...{stored_token[-5:]}")
            except Exception as e:
                print(f"   Error reading: {e}")
        else:
            print(f"❌ Not found: {token_file}")

def generate_access_token_from_request_token():
    """🔑 Generate access token from request token."""
    print("\n🔑 ACCESS TOKEN GENERATOR")
    print("=" * 50)
    
    try:
        from kiteconnect import KiteConnect
    except ImportError:
        print("❌ KiteConnect library not available")
        print("Install with: pip install kiteconnect")
        return None
    
    api_key = os.getenv('KITE_API_KEY')
    api_secret = os.getenv('KITE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ Missing API_KEY or API_SECRET in environment")
        return None
    
    print(f"📋 API Key: {api_key}")
    print(f"📋 API Secret: {api_secret[:5]}...")
    
    # Get request token from user
    request_token = input("\n🔑 Enter your request token: ").strip()
    
    if not request_token:
        print("❌ No request token provided")
        return None
    
    print(f"📋 Request Token: {request_token}")
    
    try:
        # Generate session
        kite = KiteConnect(api_key=api_key)
        session_data = kite.generate_session(request_token, api_secret=api_secret)
        
        access_token = session_data['access_token']
        user_name = session_data.get('user_name', 'Unknown')
        
        print(f"\n✅ ACCESS TOKEN GENERATED!")
        print(f"📋 Access Token: {access_token}")
        print(f"👤 User: {user_name}")
        
        # Save to .env file
        env_file = Path('.env')
        if env_file.exists():
            set_key(str(env_file), 'KITE_ACCESS_TOKEN', access_token)
            print(f"✅ Token saved to .env file")
        else:
            with open('.env', 'w') as f:
                f.write(f'KITE_API_KEY={api_key}\n')
                f.write(f'KITE_API_SECRET={api_secret}\n')
                f.write(f'KITE_ACCESS_TOKEN={access_token}\n')
            print(f"✅ Created .env file with token")
        
        # Test the token
        kite.set_access_token(access_token)
        profile = kite.profile()
        print(f"✅ Token test successful - User: {profile.get('user_name', 'Unknown')}")
        
        return access_token
        
    except Exception as e:
        print(f"❌ Token generation failed: {e}")
        return None

def test_kite_provider_initialization():
    """🧪 Test KiteDataProvider initialization."""
    print("\n🧪 KITE PROVIDER TEST")
    print("=" * 50)
    
    try:
        from kite_provider_complete import KiteDataProvider
    except ImportError:
        print("❌ KiteDataProvider not available")
        return
    
    api_key = os.getenv('KITE_API_KEY')
    access_token = os.getenv('KITE_ACCESS_TOKEN')
    
    print(f"📋 Using API Key: {api_key[:10]}...")
    print(f"📋 Using Access Token: {access_token[:10]}...{access_token[-5:]}")
    
    try:
        # Create provider
        provider = KiteDataProvider(api_key=api_key, access_token=access_token)
        print("✅ KiteDataProvider instance created")
        
        # Test initialize method
        if hasattr(provider, 'initialize'):
            result = provider.initialize()
            print(f"📊 Initialize result: {result}")
        
        # Test connection
        if hasattr(provider, 'check_health'):
            health = provider.check_health()
            print(f"📊 Health check: {health}")
        
        # Test LTP call
        if hasattr(provider, 'get_ltp'):
            try:
                ltp_result = provider.get_ltp(['NSE:NIFTY 50'])
                print(f"✅ LTP test successful: {ltp_result}")
            except Exception as ltp_error:
                print(f"❌ LTP test failed: {ltp_error}")
        
    except Exception as e:
        print(f"❌ KiteDataProvider test failed: {e}")

def fix_kite_provider():
    """🔧 Create fixed KiteDataProvider initialization."""
    print("\n🔧 KITE PROVIDER FIX")
    print("=" * 50)
    
    fix_code = '''
# Add this to your KiteDataProvider initialization in the main platform:

def _initialize_kite_provider_FIXED(self):
    """🔌 Initialize Kite provider with proper KiteConnect setup."""
    try:
        access_token = os.getenv('KITE_ACCESS_TOKEN')
        api_key = os.getenv('KITE_API_KEY')
        
        if not access_token or not api_key:
            self.logger.error("🔴 Missing API credentials")
            self.kite_provider = None
            return
        
        # Create provider
        self.kite_provider = KiteDataProvider(
            api_key=api_key,
            access_token=access_token
        )
        
        # FORCE initialization of internal KiteConnect
        if hasattr(self.kite_provider, 'initialize'):
            init_result = self.kite_provider.initialize()
            if init_result:
                self.logger.info("✅ Kite provider initialized and connected")
            else:
                self.logger.warning("⚠️ Kite provider initialization failed")
        
        # Test with a simple call
        try:
            if hasattr(self.kite_provider, 'get_ltp'):
                test_result = self.kite_provider.get_ltp(['NSE:NIFTY 50'])
                self.logger.info(f"✅ Kite connection test successful")
            
        except Exception as test_error:
            self.logger.warning(f"⚠️ Kite connection test failed: {test_error}")
            # Don't fail completely - provider might still work
            
    except Exception as e:
        self.logger.error(f"🔴 Kite provider error: {e}")
        self.kite_provider = None
'''
    
    print(fix_code)
    
    # Save fix to file
    with open('kite_provider_fix.py', 'w') as f:
        f.write(fix_code)
    print("✅ Fix saved to kite_provider_fix.py")

def validate_token_directly():
    """✅ Direct token validation."""
    print("\n✅ DIRECT TOKEN VALIDATION")
    print("=" * 50)
    
    try:
        from kiteconnect import KiteConnect
    except ImportError:
        print("❌ KiteConnect library not available")
        return False
    
    api_key = os.getenv('KITE_API_KEY')
    access_token = os.getenv('KITE_ACCESS_TOKEN')
    
    if not api_key or not access_token:
        print("❌ Missing credentials")
        return False
    
    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        
        # Test profile
        profile = kite.profile()
        print(f"✅ Profile call successful")
        print(f"👤 User: {profile.get('user_name', 'Unknown')}")
        print(f"📧 Email: {profile.get('email', 'Unknown')}")
        
        # Test LTP
        ltp_data = kite.ltp(['NSE:NIFTY 50'])
        print(f"✅ LTP call successful")
        print(f"📊 NIFTY LTP: {ltp_data}")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct validation failed: {e}")
        return False

def main():
    """🚀 Main debug function."""
    print("🔧 G6.1 TOKEN DEBUG & FIX UTILITY")
    print("=" * 60)
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check token storage
    check_token_storage()
    
    # Validate token directly
    if validate_token_directly():
        print("\n🎉 TOKEN IS VALID - Issue is in KiteDataProvider initialization")
    else:
        print("\n🔧 TOKEN ISSUES DETECTED")
        
        choice = input("\n🔑 Generate fresh access token? [y/N]: ").strip().lower()
        if choice == 'y':
            new_token = generate_access_token_from_request_token()
            if new_token:
                print(f"\n✅ New token generated: {new_token}")
    
    # Test KiteDataProvider
    test_kite_provider_initialization()
    
    # Show fix
    fix_kite_provider()
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY:")
    print("1. Check if token validation passes above")
    print("2. If token is valid but KiteDataProvider fails, apply the fix")
    print("3. If token is invalid, generate a new one")
    print("4. Replace _initialize_kite_provider method with the fixed version")
    print("=" * 60)

if __name__ == "__main__":
    main()
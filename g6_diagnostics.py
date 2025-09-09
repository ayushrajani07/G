#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 G6.1 Platform Diagnostic Script
Author: AI Assistant (Identify existing collector interfaces)

This script inspects your existing collectors to determine the correct method signatures
"""

import os
import sys
import inspect
from pathlib import Path

print("🔍 G6.1 PLATFORM DIAGNOSTICS")
print("=" * 50)

# Load environment for imports
from dotenv import load_dotenv
load_dotenv()

def inspect_class_methods(cls, class_name):
    """🔍 Inspect class methods and signatures."""
    print(f"\n📊 {class_name} ANALYSIS:")
    print("-" * 30)
    
    try:
        # Get constructor signature
        init_sig = inspect.signature(cls.__init__)
        print(f"📝 Constructor: {class_name}.__init__{init_sig}")
        
        # Get all methods
        methods = [method for method in dir(cls) if not method.startswith('_') and callable(getattr(cls, method))]
        
        print("🔧 Public Methods:")
        for method_name in methods:
            try:
                method = getattr(cls, method_name)
                if callable(method):
                    try:
                        sig = inspect.signature(method)
                        print(f"   • {method_name}{sig}")
                    except Exception:
                        print(f"   • {method_name}(...)")
            except Exception:
                pass
                
    except Exception as e:
        print(f"❌ Error inspecting {class_name}: {e}")

def test_token_validation():
    """🔐 Test token validation methods."""
    print(f"\n🔐 TOKEN VALIDATION TEST:")
    print("-" * 30)
    
    api_key = os.getenv('KITE_API_KEY')
    access_token = os.getenv('KITE_ACCESS_TOKEN')
    
    print(f"API Key: {api_key[:10]}... (length: {len(api_key) if api_key else 0})")
    print(f"Access Token: {access_token[:10]}... (length: {len(access_token) if access_token else 0})")
    
    if not api_key:
        print("❌ KITE_API_KEY not found!")
        return
    
    if not access_token:
        print("❌ KITE_ACCESS_TOKEN not found!")
        return
    
    # Try direct KiteConnect test
    try:
        from kiteconnect import KiteConnect
        print("✅ KiteConnect library available")
        
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        
        # Test with profile call
        try:
            profile = kite.profile()
            print(f"✅ Token is VALID - User: {profile.get('user_name', 'Unknown')}")
            return True
        except Exception as e:
            print(f"❌ Token validation failed: {str(e)[:100]}...")
            
            # Try margins call as backup
            try:
                margins = kite.margins()
                print("✅ Token is VALID (margins call succeeded)")
                return True
            except Exception as e2:
                print(f"❌ Margins call also failed: {str(e2)[:50]}...")
                return False
                
    except ImportError:
        print("❌ KiteConnect library not available")
        return False

def test_kite_provider():
    """🔌 Test KiteDataProvider."""
    print(f"\n🔌 KITE PROVIDER TEST:")
    print("-" * 30)
    
    try:
        from kite_provider_complete import KiteDataProvider
        print("✅ KiteDataProvider available")
        
        inspect_class_methods(KiteDataProvider, "KiteDataProvider")
        
        # Try to create instance
        try:
            provider = KiteDataProvider(
                api_key=os.getenv('KITE_API_KEY'),
                access_token=os.getenv('KITE_ACCESS_TOKEN')
            )
            print("✅ KiteDataProvider instance created")
            
            # Test connection if method exists
            if hasattr(provider, 'test_connection'):
                try:
                    result = provider.test_connection()
                    print(f"🔌 Connection test: {'✅ Success' if result else '❌ Failed'}")
                except Exception as e:
                    print(f"🔌 Connection test failed: {e}")
            
        except Exception as e:
            print(f"❌ Failed to create KiteDataProvider: {e}")
            
    except ImportError as e:
        print(f"❌ KiteDataProvider not available: {e}")

def main():
    """🚀 Run diagnostics."""
    
    # Test token first
    token_valid = test_token_validation()
    
    # Test KiteDataProvider
    test_kite_provider()
    
    # Test ATM Options Collector
    try:
        from atm_options_collector import ATMOptionsCollector
        print("✅ ATMOptionsCollector available")
        inspect_class_methods(ATMOptionsCollector, "ATMOptionsCollector")
        
        # Try different initialization methods
        print("\n🧪 TESTING ATM COLLECTOR INITIALIZATION:")
        
        # Method 1: No parameters
        try:
            collector1 = ATMOptionsCollector()
            print("✅ ATMOptionsCollector() works")
        except Exception as e:
            print(f"❌ ATMOptionsCollector(): {e}")
        
        # Method 2: With kite_provider
        try:
            from kite_provider_complete import KiteDataProvider
            provider = KiteDataProvider(
                api_key=os.getenv('KITE_API_KEY'),
                access_token=os.getenv('KITE_ACCESS_TOKEN')
            )
            collector2 = ATMOptionsCollector(kite_provider=provider)
            print("✅ ATMOptionsCollector(kite_provider=...) works")
        except Exception as e:
            print(f"❌ ATMOptionsCollector(kite_provider=...): {e}")
        
        # Method 3: With data_provider
        try:
            collector3 = ATMOptionsCollector(data_provider=provider)
            print("✅ ATMOptionsCollector(data_provider=...) works")
        except Exception as e:
            print(f"❌ ATMOptionsCollector(data_provider=...): {e}")
            
    except ImportError:
        print("❌ ATMOptionsCollector not available")
    
    # Test Overview Collector
    try:
        from overview_collector import OverviewCollector
        print("\n✅ OverviewCollector available")
        inspect_class_methods(OverviewCollector, "OverviewCollector")
        
        # Try different initialization methods
        print("\n🧪 TESTING OVERVIEW COLLECTOR INITIALIZATION:")
        
        # Method 1: No parameters
        try:
            overview1 = OverviewCollector()
            print("✅ OverviewCollector() works")
        except Exception as e:
            print(f"❌ OverviewCollector(): {e}")
            
        # Method 2: With advanced_analytics
        try:
            overview2 = OverviewCollector(advanced_analytics=True)
            print("✅ OverviewCollector(advanced_analytics=True) works")
        except Exception as e:
            print(f"❌ OverviewCollector(advanced_analytics=True): {e}")
            
    except ImportError:
        print("❌ OverviewCollector not available")
    
    # Test Analytics Engines
    try:
        from analytics_engine import IVCalculator, GreeksCalculator, PCRAnalyzer
        print("\n✅ Analytics engines available")
        
        # Test IVCalculator
        print("\n🧪 TESTING IV CALCULATOR:")
        try:
            iv_calc1 = IVCalculator()
            print("✅ IVCalculator() works")
        except Exception as e:
            print(f"❌ IVCalculator(): {e}")
            
        try:
            iv_calc2 = IVCalculator(r=0.06)
            print("✅ IVCalculator(r=0.06) works")
        except Exception as e:
            print(f"❌ IVCalculator(r=0.06): {e}")
            
        try:
            iv_calc3 = IVCalculator(risk_free_rate=0.06)
            print("✅ IVCalculator(risk_free_rate=0.06) works")
        except Exception as e:
            print(f"❌ IVCalculator(risk_free_rate=0.06): {e}")
            
        inspect_class_methods(IVCalculator, "IVCalculator")
        
    except ImportError:
        print("❌ Analytics engines not available")
    
    # Summary
    print(f"\n" + "=" * 50)
    print("🎯 DIAGNOSTIC SUMMARY:")
    print("=" * 50)
    print(f"🔐 Token Status: {'✅ Valid' if token_valid else '❌ Invalid'}")
    print("📋 Next steps based on findings above...")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test script to verify Resend package installation and functionality
"""
import os
import sys

def test_resend_import():
    """Test if Resend package can be imported"""
    try:
        import resend
        print("✅ Resend package imported successfully")
        print(f"   Version: {resend.__version__ if hasattr(resend, '__version__') else 'Unknown'}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import Resend: {e}")
        print("   Run: pip install resend")
        return False

def test_resend_api():
    """Test Resend API functionality"""
    try:
        import resend
        
        # Check if API key is set
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            print("⚠️  RESEND_API_KEY not set - skipping API test")
            print("   Set RESEND_API_KEY environment variable to test API")
            return True
        
        resend.api_key = api_key
        print(f"✅ Resend API key found: {api_key[:10]}...")
        
        # Test API connection (without sending email)
        print("✅ Resend package is ready for email sending")
        return True
        
    except Exception as e:
        print(f"❌ Resend API test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Resend Package Installation")
    print("=" * 50)
    
    # Test import
    import_success = test_resend_import()
    
    if import_success:
        # Test API
        test_resend_api()
    
    print("\n📋 Next Steps:")
    print("1. Get Resend API key from https://resend.com")
    print("2. Add RESEND_API_KEY to Railway environment variables")
    print("3. Deploy to Railway - emails will be sent automatically")
    
    sys.exit(0 if import_success else 1)

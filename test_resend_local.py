#!/usr/bin/env python3
"""
Test Resend email backend locally by simulating Railway environment
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/sandormatyas/Desktop/Projects/cleanhandy/cleanhandy')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cleanhandy.settings')
django.setup()

from django.core.mail import EmailMessage
from django.conf import settings

def test_resend_locally():
    """Test Resend backend by simulating Railway environment"""
    print("🧪 Testing Resend Backend Locally")
    print("=" * 50)
    
    # Simulate Railway environment
    os.environ["RAILWAY_ENVIRONMENT"] = "production"
    os.environ["RAILWAY_PLAN"] = "free"
    
    # Check if you have a Resend API key
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("❌ RESEND_API_KEY not set in local environment")
        print("💡 To test locally, set: export RESEND_API_KEY=re_your_key_here")
        print("💡 Or test on Railway where the API key is set")
        return False
    
    print(f"✅ RESEND_API_KEY found: {api_key[:10]}...")
    
    # Reload settings to pick up the new environment variables
    from importlib import reload
    import cleanhandy.settings
    reload(cleanhandy.settings)
    
    print(f"Email Backend: {cleanhandy.settings.EMAIL_BACKEND}")
    
    if "ResendEmailBackend" not in cleanhandy.settings.EMAIL_BACKEND:
        print("❌ Still not using Resend backend")
        return False
    
    try:
        # Test simple email
        email = EmailMessage(
            subject='🧪 Local Resend Test',
            body='<h1>Test Email</h1><p>Testing Resend backend locally.</p>',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['test@example.com'],
        )
        email.content_subtype = "html"
        
        result = email.send()
        
        if result:
            print("✅ Resend backend test successful")
            return True
        else:
            print("❌ Resend backend test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_without_api_key():
    """Test what happens without API key (console backend)"""
    print("\n🧪 Testing Console Backend (No API Key)")
    print("=" * 50)
    
    # Simulate Railway environment without API key
    os.environ["RAILWAY_ENVIRONMENT"] = "production"
    os.environ["RAILWAY_PLAN"] = "free"
    if "RESEND_API_KEY" in os.environ:
        del os.environ["RESEND_API_KEY"]
    
    # Reload settings
    from importlib import reload
    import cleanhandy.settings
    reload(cleanhandy.settings)
    
    print(f"Email Backend: {cleanhandy.settings.EMAIL_BACKEND}")
    
    try:
        email = EmailMessage(
            subject='🧪 Console Backend Test',
            body='This should be logged to console only.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['test@example.com'],
        )
        
        result = email.send()
        print(f"✅ Console backend test result: {result}")
        print("📝 Check console output above for email content")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Local Resend Backend Test")
    print("=" * 50)
    
    # Test console backend (no API key)
    console_success = test_without_api_key()
    
    # Test Resend backend (with API key)
    resend_success = test_resend_locally()
    
    print("\n📋 Results:")
    print(f"Console Backend: {'✅ Success' if console_success else '❌ Failed'}")
    print(f"Resend Backend: {'✅ Success' if resend_success else '❌ Failed'}")
    
    print("\n💡 Next Steps:")
    print("1. Add RESEND_API_KEY to Railway environment variables")
    print("2. Deploy to Railway")
    print("3. Test booking emails on Railway")
    print("4. Check Railway logs for email delivery status")

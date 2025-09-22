#!/usr/bin/env python3
"""
Simple email test to verify Resend configuration
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/sandormatyas/Desktop/Projects/cleanhandy/cleanhandy')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cleanhandy.settings')
django.setup()

from django.core.mail import send_mail, EmailMessage
from django.conf import settings

def test_simple_email():
    """Test sending a simple email"""
    print("🧪 Testing Simple Email Sending")
    print("=" * 40)
    
    # Check configuration
    print(f"Email Backend: {settings.EMAIL_BACKEND}")
    print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
    
    # Check if Resend API key is set
    api_key = os.getenv("RESEND_API_KEY")
    if api_key:
        print(f"Resend API Key: ✅ Set ({api_key[:10]}...)")
    else:
        print("Resend API Key: ❌ Not set")
        print("This will use console backend (no real delivery)")
    
    try:
        # Test simple email
        result = send_mail(
            subject='🧪 Test Email from TheCleanHandy',
            message='This is a test email to verify email delivery.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['test@example.com'],  # Dummy email
            fail_silently=False,
        )
        
        print(f"Email send result: {result}")
        
        if result:
            print("✅ Email sending function works")
        else:
            print("❌ Email sending failed")
            
    except Exception as e:
        print(f"❌ Email sending error: {e}")
        return False
    
    return True

def test_html_email():
    """Test sending HTML email (like booking emails)"""
    print("\n🧪 Testing HTML Email Sending")
    print("=" * 40)
    
    try:
        html_message = EmailMessage(
            subject='🧪 Test HTML Email from TheCleanHandy',
            body='<h1>Test HTML Email</h1><p>This is a test HTML email like the booking emails.</p>',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['test@example.com'],
        )
        html_message.content_subtype = "html"
        
        result = html_message.send()
        print(f"HTML email send result: {result}")
        
        if result:
            print("✅ HTML email sending works")
        else:
            print("❌ HTML email sending failed")
            
    except Exception as e:
        print(f"❌ HTML email sending error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Email Configuration Test")
    print("=" * 50)
    
    # Test simple email
    simple_success = test_simple_email()
    
    # Test HTML email
    html_success = test_html_email()
    
    print("\n📋 Results:")
    print(f"Simple Email: {'✅ Success' if simple_success else '❌ Failed'}")
    print(f"HTML Email: {'✅ Success' if html_success else '❌ Failed'}")
    
    if simple_success and html_success:
        print("\n🎉 Email system is working!")
        print("If you're not receiving emails:")
        print("1. Check spam/junk folder")
        print("2. Verify RESEND_API_KEY is correct")
        print("3. Check Resend dashboard for delivery status")
    else:
        print("\n❌ Email system has issues")
        print("Check the error messages above for details")

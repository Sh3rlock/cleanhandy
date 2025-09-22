#!/usr/bin/env python3
"""
Test Resend email backend with PDF attachments
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

def test_resend_with_attachment():
    """Test Resend with PDF attachment"""
    print("🧪 Testing Resend with PDF Attachment")
    print("=" * 50)
    
    # Check if we're using Resend backend
    print(f"Email Backend: {settings.EMAIL_BACKEND}")
    
    if "ResendEmailBackend" not in settings.EMAIL_BACKEND:
        print("❌ Not using Resend backend - set RESEND_API_KEY environment variable")
        return False
    
    try:
        # Create a test PDF content (simulate PDF bytes)
        test_pdf_content = b"PDF test content - this would be actual PDF bytes"
        
        # Create email with attachment
        email = EmailMessage(
            subject='🧪 Test Email with PDF Attachment',
            body='<h1>Test Email</h1><p>This email has a PDF attachment.</p>',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['test@example.com'],
        )
        email.content_subtype = "html"
        email.attach('test.pdf', test_pdf_content, 'application/pdf')
        
        # Send email
        result = email.send()
        
        if result:
            print("✅ Email with PDF attachment sent successfully")
            return True
        else:
            print("❌ Email sending failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_resend_without_attachment():
    """Test Resend without attachments"""
    print("\n🧪 Testing Resend without Attachments")
    print("=" * 50)
    
    try:
        # Create simple email without attachments
        email = EmailMessage(
            subject='🧪 Test Email without Attachments',
            body='<h1>Test Email</h1><p>This email has no attachments.</p>',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['test@example.com'],
        )
        email.content_subtype = "html"
        
        # Send email
        result = email.send()
        
        if result:
            print("✅ Email without attachments sent successfully")
            return True
        else:
            print("❌ Email sending failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Resend Email Backend Test")
    print("=" * 50)
    
    # Test without attachments
    simple_success = test_resend_without_attachment()
    
    # Test with attachments
    attachment_success = test_resend_with_attachment()
    
    print("\n📋 Results:")
    print(f"Simple Email: {'✅ Success' if simple_success else '❌ Failed'}")
    print(f"Email with PDF: {'✅ Success' if attachment_success else '❌ Failed'}")
    
    if simple_success and attachment_success:
        print("\n🎉 Resend backend is working correctly!")
    else:
        print("\n❌ Resend backend has issues")
        print("Check the error messages above for details")

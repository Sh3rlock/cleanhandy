"""
Management command to debug email delivery issues
Usage: python manage.py debug_email
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Debug email delivery configuration and test sending'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Email Delivery Debug Report")
        self.stdout.write("=" * 50)
        
        # 1. Check environment
        self.check_environment()
        
        # 2. Check email backend configuration
        self.check_email_backend()
        
        # 3. Check Resend configuration
        self.check_resend_config()
        
        # 4. Test email sending
        self.test_email_sending()
        
        self.stdout.write("\n📋 Summary:")
        self.stdout.write("If you see '✅ Email sent via Resend' but no email arrives:")
        self.stdout.write("1. Check spam/junk folder")
        self.stdout.write("2. Verify Resend API key is correct")
        self.stdout.write("3. Check Resend dashboard for delivery status")
        self.stdout.write("4. Verify sender email domain is verified in Resend")

    def check_environment(self):
        self.stdout.write("\n🌍 Environment Check:")
        is_railway = os.getenv("RAILWAY_ENVIRONMENT", "").lower() in ["production", "preview"]
        railway_plan = os.getenv("RAILWAY_PLAN", "").lower()
        
        self.stdout.write(f"   Railway Environment: {'✅ Yes' if is_railway else '❌ No'}")
        self.stdout.write(f"   Railway Plan: {railway_plan or 'Not set'}")
        
        if is_railway and railway_plan in ["free", "trial", "hobby", ""]:
            self.stdout.write("   ⚠️  Free plan detected - SMTP blocked, need Resend")

    def check_email_backend(self):
        self.stdout.write("\n📧 Email Backend Check:")
        self.stdout.write(f"   Backend: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"   From Email: {settings.DEFAULT_FROM_EMAIL}")
        
        if hasattr(settings, 'EMAIL_HOST'):
            self.stdout.write(f"   SMTP Host: {settings.EMAIL_HOST}")
            self.stdout.write(f"   SMTP Port: {settings.EMAIL_PORT}")

    def check_resend_config(self):
        self.stdout.write("\n🔑 Resend Configuration Check:")
        api_key = os.getenv("RESEND_API_KEY")
        
        if api_key:
            self.stdout.write(f"   API Key: ✅ Set ({api_key[:10]}...)")
            self.stdout.write("   Status: Ready for email sending")
        else:
            self.stdout.write("   API Key: ❌ Not set")
            self.stdout.write("   Status: Will use console backend (no delivery)")

    def test_email_sending(self):
        self.stdout.write("\n🧪 Email Sending Test:")
        
        try:
            # Test with a simple email
            result = send_mail(
                subject='🧪 Debug Test Email',
                message='This is a test email to verify email delivery.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['test@example.com'],  # Dummy email for testing
                fail_silently=False,
            )
            
            if result:
                self.stdout.write("   ✅ Email sending function works")
            else:
                self.stdout.write("   ❌ Email sending failed - no error but no delivery")
                
        except Exception as e:
            self.stdout.write(f"   ❌ Email sending failed: {str(e)}")
            
        # Test with HTML email (like booking emails)
        try:
            html_message = EmailMessage(
                subject='🧪 Debug HTML Test Email',
                body='<h1>Test HTML Email</h1><p>This is a test HTML email.</p>',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=['test@example.com'],
            )
            html_message.content_subtype = "html"
            
            result = html_message.send()
            if result:
                self.stdout.write("   ✅ HTML email sending works")
            else:
                self.stdout.write("   ❌ HTML email sending failed")
                
        except Exception as e:
            self.stdout.write(f"   ❌ HTML email sending failed: {str(e)}")

    def check_resend_domain_verification(self):
        """Check if sender domain is verified in Resend"""
        self.stdout.write("\n🌐 Domain Verification Check:")
        
        from_email = settings.DEFAULT_FROM_EMAIL
        if '@' in from_email:
            domain = from_email.split('@')[1]
            self.stdout.write(f"   Sender Domain: {domain}")
            self.stdout.write("   ⚠️  Make sure this domain is verified in Resend dashboard")
            self.stdout.write("   📍 Check: https://resend.com/domains")
        else:
            self.stdout.write("   ❌ Invalid sender email format")

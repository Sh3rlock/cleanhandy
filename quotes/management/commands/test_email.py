"""
Management command to test email delivery
Usage: python manage.py test_email your-email@example.com
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Test email delivery to verify email configuration'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address to send test email to')

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write(f"📧 Testing email delivery to: {email}")
        self.stdout.write(f"📧 Using backend: {settings.EMAIL_BACKEND}")
        
        try:
            result = send_mail(
                subject='🧪 Test Email from TheCleanHandy',
                message='This is a test email to verify email delivery is working correctly.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            if result:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Email sent successfully! Check {email} inbox.')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Email sending failed - no error but no delivery')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Email sending failed: {str(e)}')
            )
            
        # Show current configuration
        self.stdout.write("\n📋 Current Email Configuration:")
        self.stdout.write(f"   Backend: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"   From Email: {settings.DEFAULT_FROM_EMAIL}")
        
        if hasattr(settings, 'RESEND_API_KEY'):
            self.stdout.write(f"   Resend API Key: {'✅ Set' if settings.RESEND_API_KEY else '❌ Not set'}")
        
        if hasattr(settings, 'EMAIL_HOST'):
            self.stdout.write(f"   SMTP Host: {settings.EMAIL_HOST}")
            self.stdout.write(f"   SMTP Port: {settings.EMAIL_PORT}")

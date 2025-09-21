"""
Custom email backends for handling Railway SMTP restrictions
"""
import os
import logging
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.console import ConsoleEmailBackend
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.conf import settings

logger = logging.getLogger(__name__)

class RailwayAwareEmailBackend(BaseEmailBackend):
    """
    Email backend that automatically handles Railway SMTP restrictions
    Falls back to console backend when SMTP is blocked
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.smtp_backend = None
        self.console_backend = None
        self._backend = None
        
    def _get_backend(self):
        """Get the appropriate backend based on environment"""
        if self._backend is None:
            # Check if we're on Railway with SMTP restrictions
            is_railway = os.getenv("RAILWAY_ENVIRONMENT", "").lower() in ["production", "preview"]
            railway_plan = os.getenv("RAILWAY_PLAN", "").lower()
            
            if is_railway and railway_plan in ["free", "trial", "hobby", ""]:
                logger.info("🚀 Railway free/trial/hobby plan detected - using console email backend")
                self._backend = ConsoleEmailBackend(fail_silently=self.fail_silently)
            else:
                # Try SMTP first
                try:
                    self._backend = SMTPEmailBackend(fail_silently=self.fail_silently)
                    logger.info("📧 Using SMTP email backend")
                except Exception as e:
                    logger.warning(f"⚠️ SMTP backend failed, falling back to console: {e}")
                    self._backend = ConsoleEmailBackend(fail_silently=self.fail_silently)
        
        return self._backend
    
    def send_messages(self, email_messages):
        """Send messages using the appropriate backend"""
        backend = self._get_backend()
        
        try:
            return backend.send_messages(email_messages)
        except Exception as e:
            logger.error(f"❌ Email sending failed with primary backend: {e}")
            
            # Fallback to console backend if SMTP fails
            if not isinstance(backend, ConsoleEmailBackend):
                logger.info("🔄 Falling back to console email backend")
                console_backend = ConsoleEmailBackend(fail_silently=self.fail_silently)
                try:
                    return console_backend.send_messages(email_messages)
                except Exception as console_error:
                    logger.error(f"❌ Console backend also failed: {console_error}")
                    if not self.fail_silently:
                        raise console_error
                    return 0
            else:
                if not self.fail_silently:
                    raise e
                return 0
    
    def open(self):
        """Open connection using the appropriate backend"""
        backend = self._get_backend()
        return backend.open()
    
    def close(self):
        """Close connection using the appropriate backend"""
        backend = self._get_backend()
        return backend.close()


class ResendEmailBackend(BaseEmailBackend):
    """
    Email backend using Resend API (HTTPS) to bypass Railway SMTP restrictions
    Requires: pip install resend
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.api_key = os.getenv("RESEND_API_KEY")
        
        if not self.api_key:
            raise ValueError("RESEND_API_KEY environment variable is required")
    
    def send_messages(self, email_messages):
        """Send messages via Resend API"""
        try:
            import resend
            resend.api_key = self.api_key
            
            sent_count = 0
            for message in email_messages:
                try:
                    # Convert Django EmailMessage to Resend format
                    resend_message = {
                        "from": message.from_email,
                        "to": message.to,
                        "subject": message.subject,
                        "html": message.body if message.content_subtype == "html" else None,
                        "text": message.body if message.content_subtype != "html" else None,
                    }
                    
                    # Handle attachments if any
                    if hasattr(message, 'attachments') and message.attachments:
                        resend_message["attachments"] = []
                        for attachment in message.attachments:
                            resend_message["attachments"].append({
                                "filename": attachment[0],
                                "content": attachment[1],
                                "type": attachment[2] if len(attachment) > 2 else "application/octet-stream"
                            })
                    
                    # Send via Resend
                    response = resend.Emails.send(resend_message)
                    logger.info(f"✅ Email sent via Resend: {response['id']}")
                    sent_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Failed to send email via Resend: {e}")
                    if not self.fail_silently:
                        raise e
            
            return sent_count
            
        except ImportError:
            error_msg = "Resend package not installed. Run: pip install resend"
            logger.error(error_msg)
            if not self.fail_silently:
                raise ImportError(error_msg)
            return 0
        except Exception as e:
            logger.error(f"❌ Resend API error: {e}")
            if not self.fail_silently:
                raise e
            return 0

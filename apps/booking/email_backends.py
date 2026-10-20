"""Resend email backend used when Railway blocks SMTP, matching CleanHandy."""

import base64
import logging
import os

from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class ResendEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.api_key = os.environ.get("RESEND_API_KEY")
        if not self.api_key and not fail_silently:
            raise ValueError("RESEND_API_KEY is required for the Resend email backend.")

    def send_messages(self, email_messages):
        if not email_messages or not self.api_key:
            return 0
        try:
            import resend
        except ImportError:
            if not self.fail_silently:
                raise
            return 0

        resend.api_key = self.api_key
        sent = 0
        for message in email_messages:
            try:
                payload = {
                    "from": message.from_email,
                    "to": message.to,
                    "subject": message.subject,
                }
                html_content = None
                text_content = None
                for content, mimetype in getattr(message, "alternatives", []):
                    if mimetype == "text/html":
                        html_content = content
                    elif mimetype == "text/plain":
                        text_content = content
                if html_content is None and message.content_subtype == "html":
                    html_content = message.body
                else:
                    text_content = text_content or message.body
                if html_content:
                    payload["html"] = html_content
                if text_content:
                    payload["text"] = text_content
                if message.bcc:
                    payload["bcc"] = list(message.bcc)
                if message.cc:
                    payload["cc"] = list(message.cc)
                if message.attachments:
                    payload["attachments"] = []
                    for attachment in message.attachments:
                        content = attachment[1]
                        if isinstance(content, str):
                            content = content.encode()
                        payload["attachments"].append(
                            {
                                "filename": attachment[0],
                                "content": base64.b64encode(content).decode("ascii"),
                                "type": attachment[2] if len(attachment) > 2 else "application/octet-stream",
                            }
                        )
                resend.Emails.send(payload)
                sent += 1
            except Exception:
                logger.exception("Resend could not send %s", message.subject)
                if not self.fail_silently:
                    raise
        return sent

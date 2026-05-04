import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from uuid import uuid4

from app.core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class EmailDeliveryResult:
    provider: str
    message_id: str
    status: str
    error: str = ""


class EmailProvider:
    name = "base"

    def send(self, recipient: str, subject: str, body: str) -> EmailDeliveryResult:
        raise NotImplementedError


class ConsoleEmailProvider(EmailProvider):
    name = "console"

    def send(self, recipient: str, subject: str, body: str) -> EmailDeliveryResult:
        message_id = f"console-{uuid4()}"
        logger.info(
            "console email provider recipient=%s subject=%s message_id=%s body=%s",
            recipient,
            subject,
            message_id,
            body,
        )
        return EmailDeliveryResult(provider=self.name, message_id=message_id, status="sent")


class SmtpEmailProvider(EmailProvider):
    name = "smtp"

    def send(self, recipient: str, subject: str, body: str) -> EmailDeliveryResult:
        message = EmailMessage()
        message["From"] = settings.email_from
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        message_id = f"smtp-{uuid4()}"
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()
                if settings.smtp_username:
                    smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)
            return EmailDeliveryResult(provider=self.name, message_id=message_id, status="sent")
        except Exception as exc:
            return EmailDeliveryResult(provider=self.name, message_id=message_id, status="failed", error=str(exc))


def get_email_provider() -> EmailProvider:
    provider = settings.email_provider.lower().strip()
    if provider == "smtp":
        return SmtpEmailProvider()
    return ConsoleEmailProvider()

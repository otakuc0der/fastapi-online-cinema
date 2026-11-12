import logging
from email.message import EmailMessage
from pathlib import Path

import aiosmtplib
from aiosmtplib.errors import SMTPException
from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    TemplateError,
    select_autoescape,
)

from exceptions import EmailDeliveryError, EmailTemplateError
from notifications.interfaces import EmailSenderInterface

logger = logging.getLogger(__name__)


class EmailSender(EmailSenderInterface):
    def __init__(
        self,
        hostname: str,
        port: int,
        sender_email: str,
        use_tls: bool,
        start_tls: bool,
        template_dir: Path,
        activation_email_template_name: str,
        activation_complete_email_template_name: str,
        password_reset_template_name: str,
        password_reset_complete_template_name: str,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self._hostname = hostname
        self._port = port
        self._sender_email = sender_email
        self._use_tls = use_tls
        self._start_tls = start_tls
        self._env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            undefined=StrictUndefined,
        )
        self._activation_email_template_name = activation_email_template_name
        self._activation_complete_email_template_name = (
            activation_complete_email_template_name
        )
        self._password_reset_template_name = password_reset_template_name
        self._password_reset_complete_template_name = (
            password_reset_complete_template_name
        )
        self.credentials = (username, password)

    @property
    def credentials(self) -> tuple[str, str] | None:
        return self._credentials

    @credentials.setter
    def credentials(
        self,
        value: tuple[str | None, str | None] | None,
    ) -> None:
        if value is None:
            self._credentials = None
            return

        username, password = value

        if username is None and password is None:
            self._credentials = None
            return

        if username is None or password is None:
            raise ValueError("SMTP username and password must be provided together.")

        self._credentials = (username, password)

    def _render_template(
        self,
        template_name: str,
        **context: str,
    ) -> str:
        try:
            template = self._env.get_template(template_name)
            return template.render(**context)

        except (TemplateError, OSError, UnicodeError) as error:
            logger.exception(
                "Failed to render email template '%s'",
                template_name,
            )
            raise EmailTemplateError() from error

    async def _send_email(
        self,
        recipient: str,
        subject: str,
        text_content: str,
        html_content: str,
    ) -> None:
        msg = EmailMessage()
        msg["From"] = self._sender_email
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(text_content)
        msg.add_alternative(html_content, subtype="html")

        try:
            async with aiosmtplib.SMTP(
                hostname=self._hostname,
                port=self._port,
                use_tls=self._use_tls,
                start_tls=self._start_tls,
            ) as smtp:
                credentials = self.credentials

                if credentials is not None:
                    username, password = credentials
                    await smtp.login(username, password)

                await smtp.send_message(msg)

        except (SMTPException, OSError, TimeoutError) as error:
            logger.exception(
                "Failed to send email to '%s'",
                recipient,
            )
            raise EmailDeliveryError() from error

    async def send_activation_email(
        self,
        email: str,
        activation_link: str,
    ) -> None:
        html_content = self._render_template(
            self._activation_email_template_name,
            email=email,
            activation_link=activation_link,
        )

        text_content = (
            "Please activate your account using this link:\n"
            f"{activation_link}\n\n"
            "This link is valid for 24 hours."
        )

        await self._send_email(
            recipient=email,
            subject="Activate your Online Cinema account",
            text_content=text_content,
            html_content=html_content,
        )

    async def send_activation_complete_email(
        self,
        email: str,
        login_link: str,
    ) -> None:
        html_content = self._render_template(
            self._activation_complete_email_template_name,
            email=email,
            login_link=login_link,
        )

        text_content = (
            "Your Online Cinema account has been activated successfully.\n"
            f"Account email: {email}\n\n"
            "You can now log in using your email and password:\n"
            f"{login_link}"
        )

        await self._send_email(
            recipient=email,
            subject="Your Online Cinema account is activated",
            text_content=text_content,
            html_content=html_content,
        )

    async def send_password_reset_email(
        self,
        email: str,
        reset_link: str,
    ) -> None:
        html_content = self._render_template(
            self._password_reset_template_name,
            email=email,
            reset_link=reset_link,
        )

        text_content = (
            f"A password reset was requested for your account: {email}.\n\n"
            "To choose a new password, open this link:\n"
            f"{reset_link}\n\n"
            "This link is valid for 24 hours.\n"
            "If you did not request a password reset, ignore this email. "
            "Your password will remain unchanged."
        )

        await self._send_email(
            recipient=email,
            subject="Reset your Online Cinema password",
            text_content=text_content,
            html_content=html_content,
        )

    async def send_password_reset_complete_email(
        self,
        email: str,
        login_link: str,
    ) -> None:
        html_content = self._render_template(
            self._password_reset_complete_template_name,
            email=email,
            login_link=login_link,
        )

        text_content = (
            "Your Online Cinema password has been reset successfully.\n"
            f"Account email: {email}\n\n"
            "You can now log in using your new password:\n"
            f"{login_link}\n\n"
            "If you did not make this change, request another password reset "
            "immediately to secure your account."
        )

        await self._send_email(
            recipient=email,
            subject="Your Online Cinema password has been reset",
            text_content=text_content,
            html_content=html_content,
        )

from __future__ import annotations

import logging
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def _create_message(
    sender: str,
    recipients: dict,
    subject: str,
    html_body: str,
) -> MIMEMultipart:
    """MIMEMultipart 메시지 객체 생성."""
    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = ", ".join(recipients["to"])
    if recipients.get("cc"):
        msg["Cc"] = ", ".join(recipients["cc"])
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    return msg


def send_email(
    smtp_config: dict,
    recipients: dict,
    subject: str,
    html_body: str,
) -> None:
    """HTML 이메일 발송. 실패 시 예외 발생."""
    msg = _create_message(smtp_config["sender"], recipients, subject, html_body)

    all_recipients = (
        recipients["to"]
        + recipients.get("cc", [])
        + recipients.get("bcc", [])
    )

    if smtp_config.get("use_tls"):
        with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
            server.starttls()
            if smtp_config.get("password"):
                server.login(smtp_config.get("username", smtp_config["sender"]),
                             smtp_config["password"])
            server.sendmail(smtp_config["sender"], all_recipients, msg.as_string())
    else:
        with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
            if smtp_config.get("password"):
                server.login(smtp_config.get("username", smtp_config["sender"]),
                             smtp_config["password"])
            server.sendmail(smtp_config["sender"], all_recipients, msg.as_string())

    logger.info("메일 발송 성공: %s → %s", subject, all_recipients)


def send_with_retry(
    smtp_config: dict,
    recipients: dict,
    subject: str,
    html_body: str,
    max_attempts: int = 3,
    backoff_seconds: list[int] | None = None,
) -> tuple[bool, str]:
    """재시도 포함 발송. (성공여부, 에러메시지) 반환."""
    if backoff_seconds is None:
        backoff_seconds = [1, 3, 9]

    last_error = ""
    for attempt in range(max_attempts):
        try:
            send_email(smtp_config, recipients, subject, html_body)
            return True, ""
        except Exception as e:
            last_error = str(e)
            logger.warning(
                "메일 발송 실패 (시도 %d/%d): %s",
                attempt + 1, max_attempts, last_error,
            )
            if attempt < max_attempts - 1:
                wait = backoff_seconds[min(attempt, len(backoff_seconds) - 1)]
                time.sleep(wait)

    logger.error("메일 발송 최종 실패: %s", last_error)
    return False, last_error

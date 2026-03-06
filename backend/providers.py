"""
Email provider implementations.
Async functions for sending emails via Resend, Mailtrap, Gmail, and Custom SMTP.
"""

import httpx
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import make_msgid
from .models import EmailPayload, Provider, ProviderType

# ---------------------------------------------------------------------------
# Shared async HTTP client — initialised in lifespan, reused across requests
# to benefit from connection pooling and avoid per-request TLS handshakes.
# ---------------------------------------------------------------------------
_http_client: httpx.AsyncClient | None = None


def init_http_client() -> None:
    """Create the shared AsyncClient. Called once from lifespan startup."""
    global _http_client
    _http_client = httpx.AsyncClient(timeout=30.0)


async def close_http_client() -> None:
    """Close the shared AsyncClient. Called once from lifespan shutdown."""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


async def send_via_resend(payload: EmailPayload, provider: Provider) -> dict:
    """
    Send email via Resend API.
    
    Args:
        payload: Email content and metadata
        provider: Provider configuration with API key
    
    Returns:
        dict: Success response with provider_id and message_id
    
    Raises:
        Exception: If API call fails, includes status code and response body
    """
    url = "https://api.resend.com/emails"
    
    headers = {
        "Authorization": f"Bearer {provider.api_key}",
        "Content-Type": "application/json"
    }
    
    # Build request body according to Resend API schema
    body = {
        "from": payload.from_address,
        "to": payload.to,
        "subject": payload.subject
    }
    
    if payload.body_html:
        body["html"] = payload.body_html
    
    if payload.body_text:
        body["text"] = payload.body_text
    
    if payload.reply_to:
        body["reply_to"] = payload.reply_to
    
    if _http_client is None:
        raise RuntimeError("HTTP client is not initialized. Call init_http_client() first.")

    response = await _http_client.post(url, json=body, headers=headers)

    if response.status_code not in [200, 201]:
        raise RuntimeError(
            f"Resend API failed with status {response.status_code}: {response.text}"
        )

    result = response.json()

    return {
        "success": True,
        "provider_id": provider.id,
        "message_id": result.get("id", "unknown"),
        "response": result
    }


async def send_via_mailtrap(payload: EmailPayload, provider: Provider) -> dict:
    """
    Send email via Mailtrap API.
    
    Args:
        payload: Email content and metadata
        provider: Provider configuration with API token
    
    Returns:
        dict: Success response with provider_id and message_id
    
    Raises:
        Exception: If API call fails, includes status code and response body
    """
    url = "https://send.api.mailtrap.io/api/send"
    
    headers = {
        "Api-Token": provider.api_key,
        "Content-Type": "application/json"
    }
    
    # Build request body according to Mailtrap API schema
    body = {
        "from": {"email": payload.from_address},
        "to": [{"email": addr} for addr in payload.to],
        "subject": payload.subject
    }
    
    if payload.body_html:
        body["html"] = payload.body_html
    
    if payload.body_text:
        body["text"] = payload.body_text
    
    if payload.reply_to:
        body["reply_to"] = {"email": payload.reply_to}
    
    if _http_client is None:
        raise RuntimeError("HTTP client is not initialized. Call init_http_client() first.")

    response = await _http_client.post(url, json=body, headers=headers)

    if response.status_code not in [200, 201]:
        raise RuntimeError(
            f"Mailtrap API failed with status {response.status_code}: {response.text}"
        )

    result = response.json()

    return {
        "success": True,
        "provider_id": provider.id,
        "message_id": result.get("message_id", "unknown"),
        "response": result
    }


async def send_via_gmail(payload: EmailPayload, provider: Provider) -> dict:
    """
    Send email via Gmail SMTP using app password.
    
    Args:
        payload: Email content and metadata
        provider: Provider configuration with Gmail credentials
    
    Returns:
        dict: Success response with provider_id
    
    Raises:
        Exception: If SMTP connection or send fails
    """
    # Build MIME message
    if payload.body_html and payload.body_text:
        # Multipart message with both text and HTML
        message = MIMEMultipart("alternative")
        part1 = MIMEText(payload.body_text, "plain")
        part2 = MIMEText(payload.body_html, "html")
        message.attach(part1)
        message.attach(part2)
    elif payload.body_html:
        message = MIMEText(payload.body_html, "html")
    else:
        message = MIMEText(payload.body_text, "plain")
    
    message["From"] = payload.from_address
    message["To"] = ", ".join(payload.to)
    message["Subject"] = payload.subject
    
    if payload.reply_to:
        message["Reply-To"] = payload.reply_to
    
    message["Message-ID"] = make_msgid()

    try:
        # Connect to Gmail SMTP server (port 587 + STARTTLS)
        async with aiosmtplib.SMTP(hostname="smtp.gmail.com", port=587, start_tls=True) as smtp:
            await smtp.login(provider.gmail_address, provider.gmail_app_password)
            await smtp.send_message(message)

        return {
            "success": True,
            "provider_id": provider.id,
            "message_id": message["Message-ID"],
            "response": {"status": "sent via Gmail SMTP"}
        }

    except Exception as e:
        raise RuntimeError(f"Gmail SMTP failed for provider {provider.id}") from e


async def send_via_custom_smtp(payload: EmailPayload, provider: Provider) -> dict:
    """
    Send email via custom SMTP server.
    
    Args:
        payload: Email content and metadata
        provider: Provider configuration with SMTP credentials
    
    Returns:
        dict: Success response with provider_id
    
    Raises:
        Exception: If SMTP connection or send fails
    """
    # Build MIME message
    if payload.body_html and payload.body_text:
        # Multipart message with both text and HTML
        message = MIMEMultipart("alternative")
        part1 = MIMEText(payload.body_text, "plain")
        part2 = MIMEText(payload.body_html, "html")
        message.attach(part1)
        message.attach(part2)
    elif payload.body_html:
        message = MIMEText(payload.body_html, "html")
    else:
        message = MIMEText(payload.body_text, "plain")
    
    message["From"] = payload.from_address
    message["To"] = ", ".join(payload.to)
    message["Subject"] = payload.subject
    
    if payload.reply_to:
        message["Reply-To"] = payload.reply_to

    message["Message-ID"] = make_msgid()

    try:
        async with aiosmtplib.SMTP(
            hostname=provider.smtp_host,
            port=provider.smtp_port,
            use_tls=provider.smtp_use_ssl,
            start_tls=provider.smtp_use_tls
        ) as smtp:
            await smtp.login(provider.smtp_username, provider.smtp_password)
            await smtp.send_message(message)
            return {"success": True, "provider_id": provider.id}
    except Exception as e:
        raise RuntimeError(f"Custom SMTP failed for provider {provider.id}") from e


async def dispatch(payload: EmailPayload, provider: Provider) -> dict:
    """
    Dispatch email to the appropriate provider based on type.
    
    Args:
        payload: Email content and metadata
        provider: Provider configuration
    
    Returns:
        dict: Success response from the provider
    
    Raises:
        Exception: If provider type is unsupported or send fails
    """
    if provider.type == ProviderType.resend:
        return await send_via_resend(payload, provider)
    
    elif provider.type == ProviderType.mailtrap:
        return await send_via_mailtrap(payload, provider)
    
    elif provider.type == ProviderType.gmail:
        return await send_via_gmail(payload, provider)
    
    elif provider.type == ProviderType.custom_smtp:
        return await send_via_custom_smtp(payload, provider)
    
    else:
        raise ValueError(
            f"Unknown provider type '{provider.type}' for provider '{provider.id}'. "
            f"Valid types are: resend, mailtrap, gmail, custom_smtp."
        ) from None

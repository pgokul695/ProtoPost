"""
Pydantic models for the Hackathon Email Gateway.
Defines all data validation schemas for email payloads, providers, config, and logs.
"""

from enum import Enum
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from uuid import uuid4


class EmailPayload(BaseModel):
    """
    Represents an outbound email request.
    Validates that at least one body type (text or HTML) is present.
    """
    to: list[EmailStr] = Field(..., min_length=1, description="Recipient email addresses")
    from_address: EmailStr = Field(..., alias="from", description="Sender email address")
    subject: str = Field(..., min_length=1, description="Email subject line")
    body_text: str | None = Field(None, description="Plain text email body")
    body_html: str | None = Field(None, description="HTML email body")
    reply_to: EmailStr | None = Field(None, description="Reply-to address")
    attachments: list | None = Field(None, description="Email attachments (future support)")
    
    @model_validator(mode='after')
    def validate_body(self):
        """Ensure at least one body type is provided."""
        if not self.body_text and not self.body_html:
            raise ValueError("At least one of body_text or body_html must be provided")
        return self


class ProviderType(str, Enum):
    """Supported email provider types."""
    resend = "resend"
    mailtrap = "mailtrap"
    gmail = "gmail"
    custom_smtp = "custom_smtp"


class Provider(BaseModel):
    """
    Email provider configuration with conditional validation.
    Each provider type requires different credential fields.
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique provider ID")
    name: str = Field(..., min_length=1, description="Human-readable provider name")
    type: ProviderType = Field(..., description="Provider type")
    enabled: bool = Field(True, description="Whether this provider is active")
    weight: int = Field(100, ge=0, le=100, description="Load balancing weight (0-100)")
    
    # Conditional fields for different provider types
    api_key: str | None = Field(None, description="API key for Resend/Mailtrap")
    
    gmail_address: EmailStr | None = Field(None, description="Gmail account address")
    gmail_app_password: str | None = Field(None, description="Gmail app-specific password")
    
    smtp_host: str | None = Field(None, description="SMTP server hostname")
    smtp_port: int | None = Field(None, ge=1, le=65535, description="SMTP server port")
    smtp_username: str | None = Field(None, description="SMTP authentication username")
    smtp_password: str | None = Field(None, description="SMTP authentication password")
    smtp_use_tls: bool = Field(True, description="Use STARTTLS for SMTP")
    smtp_use_ssl: bool = Field(False, description="Use SSL/TLS for SMTP")
    
    @model_validator(mode='after')
    def validate_provider_credentials(self):
        """Validate that required fields are present for each provider type."""
        if self.type == ProviderType.resend:
            if not self.api_key:
                raise ValueError("api_key is required for Resend provider")
        
        elif self.type == ProviderType.mailtrap:
            if not self.api_key:
                raise ValueError("api_key is required for Mailtrap provider")
        
        elif self.type == ProviderType.gmail:
            if not self.gmail_address:
                raise ValueError("gmail_address is required for Gmail provider")
            if not self.gmail_app_password:
                raise ValueError("gmail_app_password is required for Gmail provider")
        
        elif self.type == ProviderType.custom_smtp:
            if not self.smtp_host:
                raise ValueError("smtp_host is required for Custom SMTP provider")
            if not self.smtp_port:
                raise ValueError("smtp_port is required for Custom SMTP provider")
            if not self.smtp_username:
                raise ValueError("smtp_username is required for Custom SMTP provider")
            if not self.smtp_password:
                raise ValueError("smtp_password is required for Custom SMTP provider")
        
        return self


class RoutingConfig(BaseModel):
    """Routing configuration for email dispatch."""
    mode: Literal["manual", "smart"] = Field(..., description="Routing strategy")
    sandbox: bool = Field(False, description="Sandbox mode - intercept all emails locally")


class AppConfig(BaseModel):
    """
    Complete application configuration state.
    Persisted to config.json and reloaded on every request.
    """
    providers: list[Provider] = Field(default_factory=list, description="Configured email providers")
    routing: RoutingConfig = Field(
        default_factory=lambda: RoutingConfig(mode="smart", sandbox=False),
        description="Routing configuration"
    )
    version: int = Field(1, description="Config version (auto-incremented on save)")


class EmailLog(BaseModel):
    """
    Email delivery log entry.
    Records the complete history of each email send attempt.
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique log entry ID")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    to_addresses: str = Field(..., description="Recipient addresses (JSON string)")
    from_address: str = Field(..., description="Sender address")
    subject: str = Field(..., description="Email subject")
    provider_id: str | None = Field(None, description="Provider ID used (null for sandbox)")
    provider_name: str | None = Field(None, description="Provider name used (null for sandbox)")
    status: Literal["success", "failed", "sandbox"] = Field(..., description="Delivery status")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    request_payload: str = Field(..., description="Original request payload (JSON string)")
    response_payload: str = Field(..., description="Provider response (JSON string)")
    error_trace: str | None = Field(None, description="Error traceback if failed")

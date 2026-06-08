"""
AWS SES Configuration Module
Loads and caches AWS SES settings
"""

import frappe
from dataclasses import dataclass
from typing import Optional


@dataclass
class SESConfig:
    """AWS SES Configuration"""
    enabled: bool = False
    aws_region: str = ""
    default_sender_email: str = ""
    default_sender_name: str = ""
    configuration_set_name: str = ""
    endpoint_url: str = ""
    profile_name: str = ""
    retry_mode: str = "standard"
    total_max_attempts: int = 3
    use_explicit_credentials: bool = False
    access_key_id: str = ""
    secret_access_key: str = ""
    session_token: str = ""


_config_cache: Optional[SESConfig] = None


def get_ses_config() -> SESConfig:
    """
    Load AWS SES configuration from settings
    Returns cached config if available
    """
    global _config_cache

    # Return cached config if available
    if _config_cache is not None:
        return _config_cache

    # Try to load settings
    try:
        if not frappe.db.exists("DocType", "AWS SES Settings"):
            # DocType doesn't exist yet (during install)
            return SESConfig()

        settings = frappe.get_single("AWS SES Settings")

        # Get password fields through Frappe password API
        secret_access_key = ""
        session_token = ""

        if settings.use_explicit_credentials:
            secret_access_key = settings.get_password("secret_access_key", raise_exception=False) or ""
            session_token = settings.get_password("session_token", raise_exception=False) or ""

        config = SESConfig(
            enabled=bool(settings.enabled),
            aws_region=settings.aws_region or "",
            default_sender_email=settings.default_sender_email or "",
            default_sender_name=settings.default_sender_name or "",
            configuration_set_name=settings.configuration_set_name or "",
            endpoint_url=settings.endpoint_url or "",
            profile_name=settings.profile_name or "",
            retry_mode=settings.retry_mode or "standard",
            total_max_attempts=settings.total_max_attempts or 3,
            use_explicit_credentials=bool(settings.use_explicit_credentials),
            access_key_id=settings.access_key_id or "",
            secret_access_key=secret_access_key,
            session_token=session_token,
        )

        # Validate runtime config if enabled
        if config.enabled:
            _validate_runtime_config(config)

        # Cache the config
        _config_cache = config
        return config

    except Exception as e:
        frappe.log_error(f"Error loading AWS SES config: {str(e)}", "AWS SES Config Error")
        # Return disabled config on error
        return SESConfig()


def _validate_runtime_config(config: SESConfig):
    """Validate runtime configuration"""
    if not config.aws_region:
        raise ValueError("AWS Region is required when SES is enabled")

    if not config.default_sender_email:
        raise ValueError("Default Sender Email is required when SES is enabled")

    if config.retry_mode not in ['standard', 'adaptive', 'legacy']:
        raise ValueError(f"Invalid retry mode: {config.retry_mode}")

    if config.total_max_attempts < 1:
        raise ValueError("Total Max Attempts must be at least 1")

    if config.use_explicit_credentials:
        if not config.access_key_id:
            raise ValueError("Access Key ID is required when using explicit credentials")
        if not config.secret_access_key:
            raise ValueError("Secret Access Key is required when using explicit credentials")


def clear_config_cache():
    """Clear cached configuration"""
    global _config_cache
    _config_cache = None
    frappe.cache().delete_value("ses_config_cache")


def mask_email(email: str) -> str:
    """
    Mask email address for logging (privacy-safe)
    Example: user@example.com -> u***@e***.com
    """
    if not email or "@" not in email:
        return "***"

    parts = email.split("@")
    local = parts[0]
    domain_parts = parts[1].split(".")

    masked_local = local[0] + "***" if len(local) > 0 else "***"
    masked_domain = domain_parts[0][0] + "***" if len(domain_parts[0]) > 0 else "***"
    tld = domain_parts[-1] if len(domain_parts) > 1 else "com"

    return f"{masked_local}@{masked_domain}.{tld}"

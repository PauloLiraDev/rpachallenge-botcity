"""Máscaras para dados pessoais em logs."""


def mask_email(email: str) -> str:
    """j***@dominio.com"""
    if "@" not in email:
        return "***"
    user, domain = email.split("@", 1)
    return f"{user[:1]}***@{domain}"


def mask_phone(phone: str) -> str:
    """Mantém só os 2 últimos dígitos."""
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 4:
        return "***"
    return f"***{digits[-2:]}"

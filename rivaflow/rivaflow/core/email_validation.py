"""Enhanced email validation with disposable email blocking.

This module provides robust email validation beyond basic regex:
- RFC 5322 compliant validation using email-validator library
- Disposable email domain blocking
- Configurable validation strictness
"""

from email_validator import EmailNotValidError, validate_email

# Common disposable email domains (updated list)
# Source: https://github.com/disposable-email-domains/disposable-email-domains
DISPOSABLE_EMAIL_DOMAINS = {
    # Temporary email services
    "10minutemail.com", "10minutemail.net", "guerrillamail.com",
    "mailinator.com", "maildrop.cc", "temp-mail.org", "tempmail.com",
    "throwaway.email", "yopmail.com", "getnada.com", "fakeinbox.com",
    "trashmail.com", "sharklasers.com", "guerrillamailblock.com",

    # Recently popular disposables
    "tempmail.io", "burnermail.io", "mohmal.com", "emailondeck.com",
    "mintemail.com", "mytemp.email", "temp-mail.io", "tempr.email",
    "dispostable.com", "33mail.com", "spamgourmet.com",

    # Single-use/testing domains
    "example.com", "test.com", "localhost", "invalid",

    # Ephemeral services
    "mailnesia.com", "anonbox.net", "anonymbox.com", "binkmail.com",
    "bobmail.info", "deadaddress.com", "dodgit.com", "emailsensei.com",
    "filzmail.com", "gishpuppy.com", "jetable.org", "harakirimail.com",
    "inbox.si", "klzlk.com", "mailcatch.com", "mailin8r.com",
    "mailmoat.com", "mailnull.com", "meltmail.com", "mintemail.com",
    "noclickemail.com", "pookmail.com", "quickinbox.com", "rcpt.at",
    "recode.me", "rtrtr.com", "safe-mail.net", "selfdestructingmail.com",
    "smellfear.com", "sogetthis.com", "spam.la", "spamavert.com",
    "spambox.us", "spamfree24.org", "spamgourmet.com", "spamgourmet.net",
    "spamhole.com", "spamify.com", "spammotel.com", "spaml.com",
    "tempemail.net", "tempinbox.com", "throwawayemailaddress.com",
    "tmail.ws", "tmailinator.com", "trash2009.com", "wegwerfmail.de",
    "wegwerfmail.net", "wegwerfmail.org", "wh4f.org", "whatpaas.com",
    "whyspam.me", "willselfdestruct.com", "yopmail.fr", "yopmail.net",
}


def is_disposable_email(email: str) -> bool:
    """
    Check if an email address uses a disposable email domain.

    Args:
        email: Email address to check

    Returns:
        True if email uses a disposable domain, False otherwise
    """
    try:
        domain = email.split("@")[1].lower()
        return domain in DISPOSABLE_EMAIL_DOMAINS
    except (IndexError, AttributeError):
        return False


def validate_email_address(
    email: str,
    check_deliverability: bool = False,
    allow_disposable: bool = False
) -> tuple[bool, str, dict]:
    """
    Validate an email address with comprehensive checks.

    Args:
        email: Email address to validate
        check_deliverability: Whether to check if domain has valid MX records (slower)
        allow_disposable: Whether to allow disposable email addresses

    Returns:
        Tuple of (is_valid, normalized_email, error_dict)
        - is_valid: Boolean indicating if email is valid
        - normalized_email: Normalized version of the email
        - error_dict: Dictionary with error details if invalid, or empty dict if valid

    Examples:
        >>> is_valid, normalized, errors = validate_email_address("user@Example.COM")
        >>> is_valid
        True
        >>> normalized
        "user@example.com"

        >>> is_valid, _, errors = validate_email_address("invalid")
        >>> is_valid
        False
        >>> errors["code"]
        "INVALID_FORMAT"
    """
    # Trim whitespace
    email = email.strip()

    # Basic empty check
    if not email:
        return False, "", {
            "code": "EMPTY_EMAIL",
            "message": "Email address is required"
        }

    # Use email-validator library for RFC 5322 validation
    try:
        validated = validate_email(
            email,
            check_deliverability=check_deliverability
        )
        normalized_email = validated.normalized

        # Check for disposable email domains if not allowed
        if not allow_disposable and is_disposable_email(normalized_email):
            return False, normalized_email, {
                "code": "DISPOSABLE_EMAIL",
                "message": "Disposable email addresses are not allowed. Please use a permanent email address."
            }

        # All checks passed
        return True, normalized_email, {}

    except EmailNotValidError as e:
        # Determine specific error type
        error_message = str(e)

        if "domain" in error_message.lower():
            error_code = "INVALID_DOMAIN"
            message = "Email domain is invalid"
        elif "@" not in email:
            error_code = "MISSING_AT_SIGN"
            message = "Email must contain an @ sign"
        elif email.count("@") > 1:
            error_code = "MULTIPLE_AT_SIGNS"
            message = "Email must contain only one @ sign"
        else:
            error_code = "INVALID_FORMAT"
            message = "Email format is invalid"

        return False, email, {
            "code": error_code,
            "message": message,
            "details": error_message
        }


def is_valid_email_simple(email: str, allow_disposable: bool = False) -> bool:
    """
    Simple boolean email validation (for backward compatibility).

    Args:
        email: Email address to validate
        allow_disposable: Whether to allow disposable email addresses

    Returns:
        True if valid, False otherwise
    """
    is_valid, _, _ = validate_email_address(
        email,
        check_deliverability=False,
        allow_disposable=allow_disposable
    )
    return is_valid


def normalize_email(email: str) -> str:
    """
    Normalize an email address (lowercase domain, preserve local part case).

    Args:
        email: Email address to normalize

    Returns:
        Normalized email address, or original if validation fails
    """
    is_valid, normalized, _ = validate_email_address(email)
    return normalized if is_valid else email.strip().lower()

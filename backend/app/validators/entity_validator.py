"""Entity validation logic for detecting issues and suggesting fixes."""

import re
from dataclasses import dataclass
from typing import Optional

from ..extractors.defang import is_defanged, refang
from ..extractors.ioc import PATTERNS, FILE_EXTENSIONS, COMMON_TLDS


def is_likely_filename(value: str) -> bool:
    """
    Check if a value is likely a filename rather than a domain.

    Examples:
    - malware.exe -> True (file extension, not a TLD)
    - evil.com -> False (valid TLD, even though .com is also a file extension)
    - document.pdf -> True (file extension)
    - config.json -> True (file extension)
    """
    parts = value.lower().split(".")
    if len(parts) < 2:
        return False

    extension = parts[-1]

    # If the extension is a valid TLD, it's likely a domain, not a filename
    # This handles cases like "evil.com" and "malware.com" where .com is both
    # a file extension AND a valid TLD - we prefer domain interpretation
    if extension in COMMON_TLDS:
        return False

    # If the extension is a known file extension (and not a TLD), it's a filename
    if extension in FILE_EXTENSIONS:
        return True

    return False


@dataclass
class EntitySuggestion:
    """A suggested correction for an extracted entity."""

    extracted_id: str
    suggestion_type: str  # 'refang', 'type_change'
    current_value: str
    suggested_value: Optional[str] = None
    current_type: str = ""
    suggested_type: Optional[str] = None
    reason: str = ""


def validate_entity(
    extracted_id: str,
    entity_type: str,
    value: str,
    raw_value: str
) -> Optional[EntitySuggestion]:
    """
    Validate an extracted entity and return a suggestion if issues found.

    Checks for:
    1. Defanged values that should be refanged
    2. Type mismatches (value doesn't match the declared type)

    Returns None if no issues found, or an EntitySuggestion if correction needed.
    """
    # Check 1: Is the stored value still defanged when it shouldn't be?
    if is_defanged(value):
        refanged = refang(value)
        if refanged != value:
            return EntitySuggestion(
                extracted_id=extracted_id,
                suggestion_type="refang",
                current_value=value,
                suggested_value=refanged,
                current_type=entity_type,
                reason=f"Value appears to be defanged. Suggested refanged form: {refanged}"
            )

    # Check 2: Does the value match its declared type?
    type_suggestion = check_type_mismatch(extracted_id, entity_type, value)
    if type_suggestion:
        return type_suggestion

    return None


def check_type_mismatch(
    extracted_id: str,
    declared_type: str,
    value: str
) -> Optional[EntitySuggestion]:
    """
    Check if a value matches its declared type and suggest corrections.

    Returns a suggestion if the value better matches a different type.
    """
    # Types that we can't validate with patterns (free-form text)
    # For these, we still check if the value matches a detectable pattern type
    non_pattern_types = {
        "threat_actor", "malware", "tool", "campaign",
        "registry_key", "file_path", "mutex", "user_agent",
        "asn", "country", "mitre_attack", "filename", "command"
    }

    # First, always try to detect what the value actually is based on patterns
    detected_type = detect_value_type(value)

    # Special case: Check if the value is actually a filename
    # This overrides pattern detection since "malware.exe" matches domain pattern
    # but is clearly a filename
    value_is_filename = is_likely_filename(value)
    if value_is_filename:
        if declared_type == "filename":
            # Correctly typed as filename, no suggestion needed
            return None
        else:
            return EntitySuggestion(
                extracted_id=extracted_id,
                suggestion_type="type_change",
                current_value=value,
                current_type=declared_type,
                suggested_type="filename",
                reason=f"Value appears to be a filename (has file extension) rather than {format_type(declared_type)}"
            )

    # If we detected a pattern-based type and it differs from declared type, suggest change
    if detected_type and detected_type != declared_type:
        return EntitySuggestion(
            extracted_id=extracted_id,
            suggestion_type="type_change",
            current_value=value,
            current_type=declared_type,
            suggested_type=detected_type,
            reason=f"Value appears to be {format_type(detected_type)} rather than {format_type(declared_type)}"
        )

    # For pattern-based declared types, verify the value matches the pattern
    if declared_type in PATTERNS:
        pattern = PATTERNS[declared_type]
        if pattern.fullmatch(value):
            # Value matches its declared type, no issue
            return None
        # Value doesn't match its declared pattern type
        # If we couldn't detect a better type above, we can't suggest anything specific

    # Check for hash length mismatches (more specific than pattern matching)
    if declared_type.startswith("hash_"):
        hash_suggestion = check_hash_type(extracted_id, declared_type, value)
        if hash_suggestion:
            return hash_suggestion

    return None


def detect_value_type(value: str) -> Optional[str]:
    """
    Detect the most likely type for a value based on patterns.

    Returns the detected type or None if no match.
    """
    # Order matters - check more specific patterns first
    type_order = [
        "hash_sha256",  # 64 hex chars
        "hash_sha1",    # 40 hex chars
        "hash_md5",     # 32 hex chars
        "ipv6",
        "url",
        "email",
        "cve",
        "ipv4",
        "domain",
    ]

    for type_name in type_order:
        if type_name in PATTERNS:
            pattern = PATTERNS[type_name]
            if pattern.fullmatch(value):
                return type_name

    return None


def check_hash_type(
    extracted_id: str,
    declared_type: str,
    value: str
) -> Optional[EntitySuggestion]:
    """
    Check hash type based on length.

    Common mistake: labeling a SHA256 as MD5 or vice versa.
    """
    # Only process hex strings
    if not re.fullmatch(r'[a-fA-F0-9]+', value):
        return None

    length = len(value)
    correct_type = None

    if length == 32:
        correct_type = "hash_md5"
    elif length == 40:
        correct_type = "hash_sha1"
    elif length == 64:
        correct_type = "hash_sha256"

    if correct_type and correct_type != declared_type:
        return EntitySuggestion(
            extracted_id=extracted_id,
            suggestion_type="type_change",
            current_value=value,
            current_type=declared_type,
            suggested_type=correct_type,
            reason=f"Hash length ({length} chars) indicates {format_type(correct_type)}, not {format_type(declared_type)}"
        )

    return None


def format_type(type_name: str) -> str:
    """Format a type name for display."""
    # Special case mappings for proper display names
    display_names = {
        "asn": "ASN",
        "cve": "CVE",
        "file_path": "Filepath",
        "hash_md5": "MD5",
        "hash_sha1": "SHA1",
        "hash_sha256": "SHA256",
        "ipv4": "IPv4",
        "ipv6": "IPv6",
        "mitre_attack": "ATT&CK",
        "url": "URL",
        "user_agent": "User-Agent",
    }

    if type_name in display_names:
        return display_names[type_name]

    # Default: replace underscores with spaces and title case
    return type_name.replace("_", " ").title()

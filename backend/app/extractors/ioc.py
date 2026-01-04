"""IOC (Indicator of Compromise) extraction using regex patterns."""

import re
from typing import List, Dict

from .defang import refang

# Pattern component for defanged dots: matches . or [.] or [dot] or (dot)
DOT = r'(?:\.|\[\.\]|\[dot\]|\(dot\))'

# Regex patterns for common IOCs (including defanged forms)
PATTERNS = {
    # IPv4: matches both normal and defanged (e.g., 1.2.3.4 or 1[.]2[.]3[.]4)
    "ipv4": re.compile(
        r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)' + DOT + r'){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        re.IGNORECASE
    ),
    "ipv6": re.compile(
        r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|'
        r'\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b|'
        r'\b(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}\b|'
        r'\b(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}\b|'
        r'\b(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}\b|'
        r'\b(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}\b|'
        r'\b(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}\b|'
        r'\b[0-9a-fA-F]{1,4}:(?::[0-9a-fA-F]{1,4}){1,6}\b|'
        r'\b:(?::[0-9a-fA-F]{1,4}){1,7}\b|'
        r'\b::(?:[fF]{4}:)?(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    ),
    # Domain: matches both normal and defanged
    "domain": re.compile(
        r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?' + DOT + r')+'
        r'(?:[a-zA-Z]{2,})\b',
        re.IGNORECASE
    ),
    # URL: matches both normal (http://) and defanged (hxxp://, hxxp[://])
    "url": re.compile(
        r'\b(?:hxxps?|https?)(?:://|\[://\])[^\s<>"{}|\\^`\[\]]+\b',
        re.IGNORECASE
    ),
    "hash_md5": re.compile(
        r'\b[a-fA-F0-9]{32}\b'
    ),
    "hash_sha1": re.compile(
        r'\b[a-fA-F0-9]{40}\b'
    ),
    "hash_sha256": re.compile(
        r'\b[a-fA-F0-9]{64}\b'
    ),
    # Email: matches both normal and defanged ([@] or [at])
    "email": re.compile(
        r'\b[a-zA-Z0-9._%+-]+(?:@|\[@\]|\[at\]|\(at\))'
        r'[a-zA-Z0-9.-]+' + DOT + r'[a-zA-Z]{2,}\b',
        re.IGNORECASE
    ),
    "cve": re.compile(
        r'\bCVE-\d{4}-\d{4,}\b',
        re.IGNORECASE
    ),
}

# Common false positives to filter out
FALSE_POSITIVE_DOMAINS = {
    "example.com", "example.org", "example.net",
    "localhost.localdomain", "test.com", "test.local",
}

FALSE_POSITIVE_IPS = {
    "0.0.0.0", "127.0.0.1", "255.255.255.255",
    "192.168.0.1", "192.168.1.1", "10.0.0.1",
}


def extract_iocs(content: str) -> List[Dict]:
    """
    Extract IOCs from text content, including defanged IOCs.

    Patterns match both normal and defanged forms directly.
    Matched values are refanged before storage.

    Returns a list of dicts with type, value, raw_value.
    """
    results = []
    seen = set()  # Deduplicate

    for ioc_type, pattern in PATTERNS.items():
        # Find matches in original content (patterns match defanged forms)
        for match in pattern.finditer(content):
            matched_value = match.group()

            # Refang the matched value to get the canonical form
            fanged_value = refang(matched_value)

            # Normalize the value
            normalized = normalize_ioc(ioc_type, fanged_value)

            # Skip false positives
            if is_false_positive(ioc_type, normalized):
                continue

            # Deduplicate by normalized value
            key = (ioc_type, normalized)
            if key in seen:
                continue
            seen.add(key)

            results.append({
                "type": ioc_type,
                "value": normalized,
                "raw_value": matched_value,
                "canonical_value": None,
            })

    return results


def normalize_ioc(ioc_type: str, value: str) -> str:
    """Normalize an IOC value for consistent matching."""
    if ioc_type in ("hash_md5", "hash_sha1", "hash_sha256"):
        return value.lower()
    if ioc_type == "domain":
        return value.lower().rstrip(".")
    if ioc_type == "email":
        return value.lower()
    if ioc_type == "url":
        # Remove trailing slashes and normalize
        return value.rstrip("/")
    if ioc_type == "cve":
        return value.upper()
    return value


def is_false_positive(ioc_type: str, value: str) -> bool:
    """Check if an IOC is a known false positive."""
    if ioc_type == "domain":
        # Check against false positive list
        if value in FALSE_POSITIVE_DOMAINS:
            return True
        # Filter out common TLDs that are too short
        if len(value.split(".")[0]) <= 1:
            return True

    if ioc_type == "ipv4":
        if value in FALSE_POSITIVE_IPS:
            return True
        # Filter out private IP ranges (common in docs)
        if value.startswith(("10.", "172.16.", "172.17.", "172.18.", "172.19.",
                            "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
                            "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
                            "172.30.", "172.31.", "192.168.")):
            return True

    # Filter out hashes that look like version numbers or other patterns
    if ioc_type == "hash_md5":
        # All same character is suspicious
        if len(set(value)) <= 2:
            return True

    return False

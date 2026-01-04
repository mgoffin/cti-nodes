"""Defanging and refanging utilities for IOCs."""

import re
from typing import Tuple

# Patterns for detecting and converting defanged IOCs
# Each tuple: (defanged_pattern, replacement_function_or_string)
DEFANG_PATTERNS = [
    # Protocol defanging
    (r'hxxps?', lambda m: m.group().replace('xx', 'tt').replace('XX', 'TT')),
    (r'hXXps?', lambda m: m.group().replace('XX', 'tt')),
    (r'meow', lambda m: 'http'),  # Common alternative defang

    # Bracket defanging for dots, colons, at signs
    (r'\[\.\]', '.'),
    (r'\[dot\]', '.'),
    (r'\(dot\)', '.'),
    (r'\[:\]', ':'),
    (r'\[://\]', '://'),
    (r'\[@\]', '@'),
    (r'\[at\]', '@'),
    (r'\(at\)', '@'),

    # Spaced defanging
    (r'\s+\.\s+', '.'),  # " . " -> "."
    (r'\s+@\s+', '@'),   # " @ " -> "@"
]


def refang(text: str) -> str:
    """
    Convert defanged text to standard form.

    Handles common defanging patterns:
    - hxxp:// -> http://
    - [.] -> .
    - [@] -> @
    - [dot] -> .
    - etc.

    Args:
        text: Potentially defanged text

    Returns:
        Refanged text with standard IOC formatting
    """
    result = text

    for pattern, replacement in DEFANG_PATTERNS:
        if callable(replacement):
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        else:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


def is_defanged(text: str) -> bool:
    """
    Check if text appears to contain defanged indicators.

    Args:
        text: Text to check

    Returns:
        True if any defanging patterns are detected
    """
    for pattern, _ in DEFANG_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def find_defanged_in_text(
    text: str,
    refanged_value: str,
    search_start: int = 0
) -> Tuple[str, int]:
    """
    Find the original (possibly defanged) form of a value in source text.

    Given a refanged value and approximate position, searches for the
    original defanged form in the source text.

    Args:
        text: Original text that may contain defanged IOCs
        refanged_value: The refanged (canonical) form of the IOC
        search_start: Approximate position to start searching

    Returns:
        Tuple of (original_text, position) or (refanged_value, -1) if not found
    """
    # Search window around the approximate position
    window_size = 100
    start = max(0, search_start - window_size)
    end = min(len(text), search_start + len(refanged_value) + window_size)
    search_text = text[start:end]

    # Try to find an exact match first
    pos = search_text.find(refanged_value)
    if pos != -1:
        return refanged_value, start + pos

    # Build a regex pattern that matches defanged variants
    # Escape the refanged value and replace . and @ with patterns
    pattern_parts = []
    i = 0
    escaped = re.escape(refanged_value)

    # Replace escaped special chars with patterns that match defanged forms
    escaped = escaped.replace(r'\.', r'(?:\[\.\]|\[dot\]|\(dot\)|\s*\.\s*|\.)')
    escaped = escaped.replace(r'@', r'(?:\[@\]|\[at\]|\(at\)|\s*@\s*|@)')
    escaped = escaped.replace(r'://', r'(?:\[://\]|://)')
    escaped = escaped.replace(r'http', r'(?:hxxps?|hXXps?|meow|https?)')
    escaped = escaped.replace(r'https', r'(?:hxxps|hXXps|https)')

    try:
        match = re.search(escaped, search_text, re.IGNORECASE)
        if match:
            return match.group(), start + match.start()
    except re.error:
        pass

    return refanged_value, -1


def defang(text: str) -> str:
    """
    Convert IOCs in text to defanged form for safe display/sharing.

    Args:
        text: Text containing IOCs

    Returns:
        Text with IOCs defanged
    """
    result = text

    # Defang URLs
    result = re.sub(
        r'(https?)(://)',
        lambda m: m.group(1).replace('t', 'x') + '[://]',
        result,
        flags=re.IGNORECASE
    )

    # Defang dots in domains/IPs (but not in paths after /)
    # This is a simplified version - full implementation would be smarter
    result = re.sub(r'\.(?=[a-zA-Z0-9])', '[.]', result)

    # Defang @ in emails
    result = result.replace('@', '[@]')

    return result

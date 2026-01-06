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

# Common file extensions that should NOT be treated as TLDs
FILE_EXTENSIONS = {
    # Executables and binaries
    "exe", "dll", "sys", "drv", "bin", "so", "dylib", "app", "msi", "com", "bat", "cmd", "ps1", "vbs", "js", "wsf", "scr",
    # Documents
    "doc", "docx", "xls", "xlsx", "ppt", "pptx", "pdf", "rtf", "odt", "ods", "odp", "txt", "csv", "xml", "json", "yaml", "yml",
    # Archives
    "zip", "rar", "7z", "tar", "gz", "bz2", "xz", "cab", "iso", "dmg",
    # Images
    "jpg", "jpeg", "png", "gif", "bmp", "ico", "svg", "webp", "tiff", "psd",
    # Audio/Video
    "mp3", "mp4", "wav", "avi", "mkv", "mov", "wmv", "flv", "webm",
    # Code/Scripts
    "py", "pyc", "pyo", "rb", "pl", "sh", "bash", "php", "asp", "aspx", "jsp", "java", "class", "jar",
    "c", "cpp", "h", "hpp", "cs", "go", "rs", "swift", "kt", "scala", "ts", "tsx", "jsx", "vue", "svelte",
    # Config/Data
    "ini", "cfg", "conf", "config", "log", "dat", "db", "sql", "sqlite", "bak",
    # Web
    "html", "htm", "css", "scss", "sass", "less",
    # Other common extensions
    "tmp", "temp", "swp", "lock", "pid", "cache", "map",
}

# Valid TLDs that are commonly seen in threat intel (subset of IANA list)
# This helps distinguish real domains from filenames
COMMON_TLDS = {
    # Generic TLDs
    "com", "net", "org", "info", "biz", "name", "pro",
    # Country code TLDs commonly abused
    "ru", "cn", "tk", "ml", "ga", "cf", "gq", "cc", "pw", "ws", "su", "to", "tv", "fm", "am", "la", "ly", "me", "co", "io", "ai", "app",
    # New gTLDs commonly seen
    "xyz", "top", "club", "online", "site", "website", "space", "tech", "store", "shop", "live", "life", "work", "cloud", "download",
    # Country codes
    "uk", "de", "fr", "it", "es", "nl", "be", "at", "ch", "pl", "cz", "se", "no", "dk", "fi", "pt", "gr", "ie", "au", "nz", "ca", "br", "mx", "ar", "jp", "kr", "in", "sg", "hk", "tw", "ph", "my", "th", "vn", "id", "za", "eg", "ng", "ke", "ua", "kz", "ir", "sa", "ae", "il", "tr",
    # US specific
    "us", "gov", "mil", "edu",
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
            start_pos = match.start()

            # Refang the matched value to get the canonical form
            fanged_value = refang(matched_value)

            # Normalize the value
            normalized = normalize_ioc(ioc_type, fanged_value)

            # Skip false positives (pass content and position for context checks)
            if is_false_positive(ioc_type, normalized, content, start_pos):
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


def is_false_positive(ioc_type: str, value: str, content: str = "", start_pos: int = 0) -> bool:
    """Check if an IOC is a known false positive."""
    if ioc_type == "domain":
        # Check against false positive list
        if value in FALSE_POSITIVE_DOMAINS:
            return True

        # Filter out common TLDs that are too short
        if len(value.split(".")[0]) <= 1:
            return True

        # Check if it's likely a filename based on extension
        parts = value.lower().split(".")
        if len(parts) >= 2:
            extension = parts[-1]

            # If the extension is a known file extension and NOT a valid TLD, it's a filename
            if extension in FILE_EXTENSIONS and extension not in COMMON_TLDS:
                return True

            # If it looks like a filename (single part before extension), check more carefully
            if len(parts) == 2:
                # Single dot like "malware.exe" - likely a filename
                if extension in FILE_EXTENSIONS:
                    return True
                # If extension is not a known TLD, likely a filename
                if extension not in COMMON_TLDS:
                    return True

        # Check context: is this preceded by a path separator?
        if start_pos > 0 and content:
            # Look at character before the match
            char_before = content[start_pos - 1] if start_pos > 0 else ""
            # Path separators indicate this is part of a file path
            if char_before in ("/", "\\"):
                return True

            # Look at more context before the match (up to 20 chars)
            context_start = max(0, start_pos - 20)
            context_before = content[context_start:start_pos].lower()

            # Common path patterns
            path_indicators = [
                "c:\\", "d:\\", "e:\\",  # Windows drive letters
                "/usr/", "/var/", "/tmp/", "/home/", "/etc/", "/opt/", "/bin/", "/lib/",  # Unix paths
                "\\users\\", "\\windows\\", "\\system32\\", "\\program files",  # Windows paths
                "\\appdata\\", "\\temp\\", "\\documents\\",
                "./", "../",  # Relative paths
            ]
            for indicator in path_indicators:
                if indicator in context_before:
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

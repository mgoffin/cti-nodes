"""Tests for entity validation logic."""

import pytest
from app.validators.entity_validator import (
    check_type_mismatch,
    detect_value_type,
    format_type,
    is_likely_filename,
    validate_entity,
)


class TestIsLikelyFilename:
    """Tests for filename detection."""

    def test_exe_is_filename(self):
        assert is_likely_filename("malware.exe") is True

    def test_dll_is_filename(self):
        assert is_likely_filename("payload.dll") is True

    def test_ps1_is_filename(self):
        assert is_likely_filename("script.ps1") is True

    def test_pdf_is_filename(self):
        assert is_likely_filename("document.pdf") is True

    def test_json_is_filename(self):
        assert is_likely_filename("config.json") is True

    def test_com_is_domain_not_filename(self):
        """Even though .com is a file extension, it's also a TLD so prefer domain."""
        assert is_likely_filename("evil.com") is False

    def test_net_is_domain_not_filename(self):
        assert is_likely_filename("malware.net") is False

    def test_org_is_domain_not_filename(self):
        assert is_likely_filename("bad.org") is False

    def test_io_is_domain_not_filename(self):
        assert is_likely_filename("test.io") is False

    def test_no_extension(self):
        assert is_likely_filename("malware") is False

    def test_unknown_extension(self):
        assert is_likely_filename("file.xyz123") is False


class TestDetectValueType:
    """Tests for automatic type detection."""

    def test_detect_ipv4(self):
        assert detect_value_type("192.168.1.1") == "ipv4"
        assert detect_value_type("8.8.8.8") == "ipv4"
        assert detect_value_type("10.0.0.1") == "ipv4"

    def test_detect_ipv6(self):
        assert detect_value_type("2001:0db8:85a3:0000:0000:8a2e:0370:7334") == "ipv6"

    def test_detect_domain(self):
        assert detect_value_type("evil.com") == "domain"
        assert detect_value_type("subdomain.evil.com") == "domain"
        assert detect_value_type("example.org") == "domain"

    def test_detect_url(self):
        assert detect_value_type("https://evil.com/payload") == "url"
        assert detect_value_type("http://192.168.1.1/malware") == "url"

    def test_detect_hash_md5(self):
        assert detect_value_type("d41d8cd98f00b204e9800998ecf8427e") == "hash_md5"

    def test_detect_hash_sha1(self):
        assert detect_value_type("da39a3ee5e6b4b0d3255bfef95601890afd80709") == "hash_sha1"

    def test_detect_hash_sha256(self):
        assert detect_value_type("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855") == "hash_sha256"

    def test_detect_email(self):
        assert detect_value_type("attacker@evil.com") == "email"

    def test_detect_cve(self):
        assert detect_value_type("CVE-2023-12345") == "cve"
        assert detect_value_type("CVE-2024-0001") == "cve"


class TestCheckTypeMismatch:
    """Tests for type mismatch detection."""

    # Correctly typed values should return None
    def test_correct_ipv4(self):
        assert check_type_mismatch("id", "ipv4", "192.168.1.1") is None

    def test_correct_domain(self):
        assert check_type_mismatch("id", "domain", "evil.com") is None

    def test_correct_filename(self):
        assert check_type_mismatch("id", "filename", "malware.exe") is None

    def test_correct_hash_md5(self):
        assert check_type_mismatch("id", "hash_md5", "d41d8cd98f00b204e9800998ecf8427e") is None

    def test_correct_hash_sha1(self):
        assert check_type_mismatch("id", "hash_sha1", "da39a3ee5e6b4b0d3255bfef95601890afd80709") is None

    def test_correct_hash_sha256(self):
        assert check_type_mismatch("id", "hash_sha256", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855") is None

    def test_correct_email(self):
        assert check_type_mismatch("id", "email", "user@example.com") is None

    def test_correct_cve(self):
        assert check_type_mismatch("id", "cve", "CVE-2023-12345") is None

    def test_correct_url(self):
        assert check_type_mismatch("id", "url", "https://evil.com/payload") is None

    # Filename detection from wrong types
    def test_filename_typed_as_domain(self):
        result = check_type_mismatch("id", "domain", "malware.exe")
        assert result is not None
        assert result.suggested_type == "filename"

    def test_filename_typed_as_hash_md5(self):
        result = check_type_mismatch("id", "hash_md5", "payload.dll")
        assert result is not None
        assert result.suggested_type == "filename"

    def test_filename_typed_as_ipv4(self):
        result = check_type_mismatch("id", "ipv4", "script.ps1")
        assert result is not None
        assert result.suggested_type == "filename"

    # Domain detection from filename type
    def test_domain_typed_as_filename(self):
        result = check_type_mismatch("id", "filename", "evil.com")
        assert result is not None
        assert result.suggested_type == "domain"

    def test_domain_net_typed_as_filename(self):
        result = check_type_mismatch("id", "filename", "malware.net")
        assert result is not None
        assert result.suggested_type == "domain"

    # IP detection from wrong types
    def test_ipv4_typed_as_filename(self):
        result = check_type_mismatch("id", "filename", "192.168.1.1")
        assert result is not None
        assert result.suggested_type == "ipv4"

    def test_ipv4_typed_as_domain(self):
        result = check_type_mismatch("id", "domain", "8.8.8.8")
        assert result is not None
        assert result.suggested_type == "ipv4"

    def test_ipv4_typed_as_hash(self):
        result = check_type_mismatch("id", "hash_md5", "10.0.0.1")
        assert result is not None
        assert result.suggested_type == "ipv4"

    # Hash type mismatches
    def test_md5_typed_as_sha256(self):
        result = check_type_mismatch("id", "hash_sha256", "d41d8cd98f00b204e9800998ecf8427e")
        assert result is not None
        assert result.suggested_type == "hash_md5"

    def test_sha1_typed_as_md5(self):
        result = check_type_mismatch("id", "hash_md5", "da39a3ee5e6b4b0d3255bfef95601890afd80709")
        assert result is not None
        assert result.suggested_type == "hash_sha1"

    def test_sha256_typed_as_sha1(self):
        result = check_type_mismatch("id", "hash_sha1", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        assert result is not None
        assert result.suggested_type == "hash_sha256"

    # URL detection
    def test_url_typed_as_domain(self):
        result = check_type_mismatch("id", "domain", "https://evil.com/payload")
        assert result is not None
        assert result.suggested_type == "url"

    # Email detection
    def test_email_typed_as_domain(self):
        result = check_type_mismatch("id", "domain", "attacker@evil.com")
        assert result is not None
        assert result.suggested_type == "email"

    # CVE detection
    def test_cve_typed_as_domain(self):
        result = check_type_mismatch("id", "domain", "CVE-2024-1234")
        assert result is not None
        assert result.suggested_type == "cve"

    def test_cve_typed_as_hash(self):
        result = check_type_mismatch("id", "hash_md5", "CVE-2023-99999")
        assert result is not None
        assert result.suggested_type == "cve"

    # Non-pattern types with detectable values
    def test_ipv4_typed_as_threat_actor(self):
        result = check_type_mismatch("id", "threat_actor", "192.168.1.1")
        assert result is not None
        assert result.suggested_type == "ipv4"

    def test_domain_typed_as_malware(self):
        result = check_type_mismatch("id", "malware", "evil.com")
        assert result is not None
        assert result.suggested_type == "domain"

    def test_url_typed_as_tool(self):
        result = check_type_mismatch("id", "tool", "https://evil.com/payload")
        assert result is not None
        assert result.suggested_type == "url"

    def test_filename_typed_as_campaign(self):
        result = check_type_mismatch("id", "campaign", "malware.exe")
        assert result is not None
        assert result.suggested_type == "filename"


class TestValidateEntity:
    """Tests for the main validate_entity function."""

    def test_valid_entity_returns_none(self):
        result = validate_entity("id", "ipv4", "192.168.1.1", "192.168.1.1")
        assert result is None

    def test_type_mismatch_returns_suggestion(self):
        result = validate_entity("id", "domain", "malware.exe", "malware.exe")
        assert result is not None
        assert result.suggestion_type == "type_change"
        assert result.suggested_type == "filename"

    def test_defanged_value_returns_refang_suggestion(self):
        result = validate_entity("id", "ipv4", "192[.]168[.]1[.]1", "192[.]168[.]1[.]1")
        assert result is not None
        assert result.suggestion_type == "refang"
        assert result.suggested_value == "192.168.1.1"


class TestFormatType:
    """Tests for type name formatting."""

    def test_format_asn(self):
        assert format_type("asn") == "ASN"

    def test_format_cve(self):
        assert format_type("cve") == "CVE"

    def test_format_file_path(self):
        assert format_type("file_path") == "Filepath"

    def test_format_hash_md5(self):
        assert format_type("hash_md5") == "MD5"

    def test_format_hash_sha1(self):
        assert format_type("hash_sha1") == "SHA1"

    def test_format_hash_sha256(self):
        assert format_type("hash_sha256") == "SHA256"

    def test_format_ipv4(self):
        assert format_type("ipv4") == "IPv4"

    def test_format_ipv6(self):
        assert format_type("ipv6") == "IPv6"

    def test_format_mitre_attack(self):
        assert format_type("mitre_attack") == "ATT&CK"

    def test_format_url(self):
        assert format_type("url") == "URL"

    def test_format_user_agent(self):
        assert format_type("user_agent") == "User-Agent"

    def test_format_domain(self):
        """Default formatting for non-special types."""
        assert format_type("domain") == "Domain"

    def test_format_threat_actor(self):
        """Default formatting for multi-word types."""
        assert format_type("threat_actor") == "Threat Actor"

    def test_format_filename(self):
        assert format_type("filename") == "Filename"

    def test_format_email(self):
        assert format_type("email") == "Email"

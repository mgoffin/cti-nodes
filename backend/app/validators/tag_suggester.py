"""Tag suggestion logic based on content analysis and extracted entities."""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class TagSuggestion:
    """A suggested tag for a node."""

    tag_name: str
    tag_value: str
    reason: str
    confidence: float = 0.8  # How confident we are in this suggestion


# Patterns for detecting content types that warrant specific tags
CONTENT_PATTERNS = {
    # Security report types
    "report_type": [
        (r"\b(incident\s+report|security\s+incident)\b", "incident", "Content mentions security incident"),
        (r"\b(threat\s+intelligence|threat\s+intel|TI\s+report)\b", "threat_intel", "Content is threat intelligence"),
        (r"\b(malware\s+analysis|malware\s+report)\b", "malware_analysis", "Content is malware analysis"),
        (r"\b(vulnerability\s+assessment|vuln\s+assessment)\b", "vulnerability", "Content discusses vulnerabilities"),
        (r"\b(phishing|spear[\s-]?phishing)\b", "phishing", "Content discusses phishing"),
        (r"\b(ransomware)\b", "ransomware", "Content mentions ransomware"),
        (r"\b(APT|advanced\s+persistent\s+threat)\b", "apt", "Content discusses APT activity"),
        (r"\b(data\s+breach|data\s+leak)\b", "data_breach", "Content mentions data breach"),
        (r"\b(DDoS|denial\s+of\s+service)\b", "ddos", "Content discusses DDoS"),
        (r"\b(zero[\s-]?day|0[\s-]?day)\b", "zero_day", "Content mentions zero-day"),
    ],
    # Severity indicators
    "severity": [
        (r"\b(critical|severe|emergency)\b", "critical", "Content indicates critical severity"),
        (r"\b(high\s+priority|high\s+severity|urgent)\b", "high", "Content indicates high severity"),
        (r"\b(medium\s+priority|moderate)\b", "medium", "Content indicates medium severity"),
        (r"\b(low\s+priority|minor)\b", "low", "Content indicates low severity"),
    ],
    # Status indicators
    "status": [
        (r"\b(ongoing|active|in[\s-]?progress)\b", "active", "Content indicates ongoing activity"),
        (r"\b(resolved|mitigated|contained)\b", "resolved", "Content indicates resolved status"),
        (r"\b(investigating|under\s+investigation)\b", "investigating", "Content indicates investigation"),
    ],
    # Target sectors
    "sector": [
        (r"\b(financial|banking|finance)\s+(sector|industry|institution)?\b", "financial", "Content targets financial sector"),
        (r"\b(healthcare|medical|hospital)\s+(sector|industry)?\b", "healthcare", "Content targets healthcare sector"),
        (r"\b(government|federal|state\s+agency)\b", "government", "Content targets government sector"),
        (r"\b(energy|utilities|power\s+grid)\b", "energy", "Content targets energy sector"),
        (r"\b(retail|e[\s-]?commerce)\b", "retail", "Content targets retail sector"),
        (r"\b(education|university|school)\b", "education", "Content targets education sector"),
        (r"\b(manufacturing|industrial)\b", "manufacturing", "Content targets manufacturing sector"),
        (r"\b(telecom|telecommunications)\b", "telecom", "Content targets telecom sector"),
    ],
    # Geographic indicators
    "region": [
        (r"\b(North\s+America|United\s+States|USA|US-based)\b", "north_america", "Content mentions North America"),
        (r"\b(Europe|European\s+Union|EU)\b", "europe", "Content mentions Europe"),
        (r"\b(Asia[\s-]?Pacific|APAC)\b", "apac", "Content mentions Asia-Pacific"),
        (r"\b(Middle\s+East|MENA)\b", "middle_east", "Content mentions Middle East"),
        (r"\b(Russia|Russian)\b", "russia", "Content mentions Russia"),
        (r"\b(China|Chinese|PRC)\b", "china", "Content mentions China"),
        (r"\b(Iran|Iranian)\b", "iran", "Content mentions Iran"),
        (r"\b(North\s+Korea|DPRK)\b", "north_korea", "Content mentions North Korea"),
    ],
}

# Entity type to tag mappings
ENTITY_TYPE_TAGS = {
    "threat_actor": ("attribution", "Contains threat actor attribution"),
    "malware": ("malware", "Contains malware indicators"),
    "cve": ("vulnerability", "Contains CVE references"),
    "mitre_attack": ("mitre_att&ck", "Contains MITRE ATT&CK references"),
}


def suggest_tags_from_content(content: str, existing_tags: list[dict]) -> list[TagSuggestion]:
    """
    Analyze content and suggest relevant tags.

    Args:
        content: The node's text content
        existing_tags: List of existing tags (dicts with 'name' and 'value')

    Returns:
        List of tag suggestions
    """
    suggestions = []
    existing_tag_set = {(t["name"].lower(), t["value"].lower()) for t in existing_tags}
    content_lower = content.lower()

    for tag_name, patterns in CONTENT_PATTERNS.items():
        for pattern, value, reason in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # Check if this tag already exists
                if (tag_name.lower(), value.lower()) not in existing_tag_set:
                    suggestions.append(TagSuggestion(
                        tag_name=tag_name,
                        tag_value=value,
                        reason=reason,
                        confidence=0.8
                    ))
                    # Only suggest one value per tag name category
                    break

    return suggestions


def suggest_tags_from_entities(
    extracted: list[dict],
    existing_tags: list[dict]
) -> list[TagSuggestion]:
    """
    Suggest tags based on extracted entities.

    Args:
        extracted: List of extracted entities (dicts with 'type', 'value')
        existing_tags: List of existing tags

    Returns:
        List of tag suggestions
    """
    suggestions = []
    existing_tag_set = {(t["name"].lower(), t["value"].lower()) for t in existing_tags}
    suggested_set = set()  # Avoid duplicate suggestions

    # Count entity types
    entity_type_counts = {}
    for entity in extracted:
        etype = entity["type"]
        entity_type_counts[etype] = entity_type_counts.get(etype, 0) + 1

    # Suggest tags based on entity presence
    for entity_type, (tag_name, reason) in ENTITY_TYPE_TAGS.items():
        if entity_type in entity_type_counts:
            tag_value = "true"
            if (tag_name.lower(), tag_value.lower()) not in existing_tag_set:
                key = (tag_name, tag_value)
                if key not in suggested_set:
                    suggested_set.add(key)
                    suggestions.append(TagSuggestion(
                        tag_name=tag_name,
                        tag_value=tag_value,
                        reason=f"{reason} ({entity_type_counts[entity_type]} found)",
                        confidence=0.9
                    ))

    # Suggest IOC-related tags based on counts
    ioc_types = ["ipv4", "ipv6", "domain", "url", "hash_md5", "hash_sha1", "hash_sha256", "email"]
    total_iocs = sum(entity_type_counts.get(t, 0) for t in ioc_types)

    if total_iocs > 0:
        if ("iocs", "true") not in existing_tag_set:
            suggestions.append(TagSuggestion(
                tag_name="iocs",
                tag_value="true",
                reason=f"Contains IOC indicators ({total_iocs} found)",
                confidence=0.9
            ))

    return suggestions


def get_tag_suggestions(
    content: str,
    extracted: list[dict],
    existing_tags: list[dict]
) -> list[TagSuggestion]:
    """
    Get all tag suggestions for a node.

    Args:
        content: The node's text content
        extracted: List of extracted entities
        existing_tags: List of existing tags

    Returns:
        Combined list of unique tag suggestions
    """
    suggestions = []
    seen = set()

    # Get content-based suggestions
    content_suggestions = suggest_tags_from_content(content, existing_tags)
    for s in content_suggestions:
        key = (s.tag_name.lower(), s.tag_value.lower())
        if key not in seen:
            seen.add(key)
            suggestions.append(s)

    # Get entity-based suggestions
    entity_suggestions = suggest_tags_from_entities(extracted, existing_tags)
    for s in entity_suggestions:
        key = (s.tag_name.lower(), s.tag_value.lower())
        if key not in seen:
            seen.add(key)
            suggestions.append(s)

    # Sort by confidence (highest first)
    suggestions.sort(key=lambda x: x.confidence, reverse=True)

    return suggestions

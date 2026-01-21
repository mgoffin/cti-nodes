"""Entity suggestion logic for finding entities from other nodes in current content."""

import re
from dataclasses import dataclass
from typing import List


@dataclass
class ExtractedEntitySuggestion:
    """A suggested entity to extract based on other nodes in the graph."""

    entity_type: str
    entity_value: str
    reason: str
    source_node_id: str
    confidence: float = 0.9


def get_extracted_entity_suggestions(
    content: str,
    all_entities_in_graph: List[dict],
    existing_extracted: List[dict],
    node_id: str
) -> List[ExtractedEntitySuggestion]:
    """
    Suggest entities to extract based on entities found in other nodes.

    Args:
        content: The node's content to analyze
        all_entities_in_graph: List of dicts with 'type', 'value', 'node_id' from other nodes
        existing_extracted: List of existing extracted entities for this node
        node_id: Current node's ID (to exclude its own entities from suggestions)

    Returns:
        List of entity suggestions
    """
    suggestions = []
    suggested_set = set()  # Avoid duplicate suggestions
    
    # Build set of existing entity values (normalized)
    existing_values = {e["value"].lower() for e in existing_extracted}
    
    # Search content for entities from other nodes
    content_lower = content.lower()
    
    for entity in all_entities_in_graph:
        # Skip entities from the current node
        if entity["node_id"] == node_id:
            continue
            
        entity_value = entity["value"]
        entity_type = entity["type"]
        source_node_id = entity["node_id"]
        
        # Skip if already extracted
        if entity_value.lower() in existing_values:
            continue
            
        # Skip if already suggested
        key = (entity_type, entity_value.lower())
        if key in suggested_set:
            continue
        
        # Check if this entity value appears in the content
        # Use word boundaries for better matching
        if _value_appears_in_content(entity_value, content_lower):
            suggested_set.add(key)
            
            # Build reason
            reason = f"Found in another node (appears in content)"
            
            suggestions.append(ExtractedEntitySuggestion(
                entity_type=entity_type,
                entity_value=entity_value,
                reason=reason,
                source_node_id=source_node_id,
                confidence=0.9
            ))
    
    # Sort by confidence (descending) and then alphabetically
    suggestions.sort(key=lambda s: (-s.confidence, s.entity_type, s.entity_value))
    
    return suggestions


def _value_appears_in_content(value: str, content_lower: str) -> bool:
    """
    Check if a value appears in the content.
    
    Uses case-insensitive matching and handles special characters.
    For multi-word values, requires exact phrase match.
    For single words, uses word boundaries when possible.
    """
    value_lower = value.lower()
    
    # Simple substring check first
    if value_lower not in content_lower:
        return False
    
    # For very short values (< 3 chars), require word boundaries
    if len(value_lower) < 3:
        # Use word boundaries to avoid false positives
        pattern = r'\b' + re.escape(value_lower) + r'\b'
        return bool(re.search(pattern, content_lower, re.IGNORECASE))
    
    # For IPs, domains, hashes, emails, etc., exact match is fine
    # since they're unique enough
    if _is_technical_value(value):
        return True
    
    # For longer text values, use word boundaries
    # This helps with threat actors, malware names, etc.
    if ' ' in value_lower:
        # Multi-word phrase - check for exact phrase
        return value_lower in content_lower
    else:
        # Single word - use word boundaries
        pattern = r'\b' + re.escape(value_lower) + r'\b'
        return bool(re.search(pattern, content_lower, re.IGNORECASE))


def _is_technical_value(value: str) -> bool:
    """
    Check if a value is a technical indicator (IP, domain, hash, etc.)
    that doesn't need word boundary checking.
    """
    # Check for IP-like patterns
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', value):
        return True
    
    # Check for hash-like patterns (all hex)
    if re.match(r'^[a-fA-F0-9]{32,}$', value):
        return True
    
    # Check for domain-like patterns
    if '.' in value and not ' ' in value:
        parts = value.split('.')
        if len(parts) >= 2 and all(part.replace('-', '').isalnum() for part in parts):
            return True
    
    # Check for email-like patterns
    if '@' in value:
        return True
    
    # Check for URL-like patterns
    if value.startswith(('http://', 'https://', 'ftp://')):
        return True
    
    return False

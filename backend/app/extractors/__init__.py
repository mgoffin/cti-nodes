"""Extractors for IOCs and named entities."""

from .ioc import extract_iocs
from .entities import extract_entities
from .defang import refang, is_defanged, defang


async def extract_all(content: str) -> list[dict]:
    """
    Extract all IOCs and entities from content.

    Returns a list of dicts with:
    - type: the extraction type (ipv4, domain, hash_sha256, threat_actor, etc.)
    - value: normalized value
    - raw_value: original value as found
    - canonical_value: canonical name for aliases (e.g., threat actors)
    """
    results = []

    # Extract IOCs
    iocs = extract_iocs(content)
    results.extend(iocs)

    # Extract named entities
    entities = await extract_entities(content)
    results.extend(entities)

    return results


__all__ = [
    "extract_all",
    "extract_iocs",
    "extract_entities",
    "refang",
    "is_defanged",
    "defang",
]

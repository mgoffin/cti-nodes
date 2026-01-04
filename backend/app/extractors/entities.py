"""Named entity extraction for threat actors, malware, and tools."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

# Cache for loaded data
_threat_actors: Optional[Dict[str, str]] = None  # alias -> canonical
_malware: Optional[set] = None
_tools: Optional[set] = None


def _load_threat_actors() -> Dict[str, str]:
    """Load threat actor aliases from data file."""
    global _threat_actors
    if _threat_actors is not None:
        return _threat_actors

    data_path = Path(__file__).parent.parent / "data" / "threat_actors.json"
    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            _threat_actors = {}
            for actor in data.get("actors", []):
                canonical = actor["canonical_name"]
                # Map canonical name to itself
                _threat_actors[canonical.lower()] = canonical
                # Map all aliases to canonical
                for alias in actor.get("aliases", []):
                    _threat_actors[alias.lower()] = canonical
    else:
        _threat_actors = {}

    return _threat_actors


def _load_malware() -> set:
    """Load malware names from data file."""
    global _malware
    if _malware is not None:
        return _malware

    data_path = Path(__file__).parent.parent / "data" / "malware.json"
    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            _malware = {m.lower() for m in data.get("malware", [])}
    else:
        _malware = set()

    return _malware


def _load_tools() -> set:
    """Load tool names from data file."""
    global _tools
    if _tools is not None:
        return _tools

    data_path = Path(__file__).parent.parent / "data" / "tools.json"
    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            _tools = {t.lower() for t in data.get("tools", [])}
    else:
        _tools = set()

    return _tools


async def extract_entities(content: str) -> List[Dict]:
    """
    Extract named entities from content.

    Returns a list of dicts with type, value, raw_value, canonical_value.
    """
    results = []
    seen = set()

    # Load reference data
    threat_actors = _load_threat_actors()
    malware = _load_malware()
    tools = _load_tools()

    # Tokenize content into words and multi-word phrases
    words = extract_words_and_phrases(content)

    for word, raw in words:
        word_lower = word.lower()

        # Check for threat actors
        if word_lower in threat_actors:
            canonical = threat_actors[word_lower]
            key = ("threat_actor", canonical)
            if key not in seen:
                seen.add(key)
                results.append({
                    "type": "threat_actor",
                    "value": canonical,
                    "raw_value": raw,
                    "canonical_value": canonical,
                })

        # Check for malware
        if word_lower in malware:
            key = ("malware", word_lower)
            if key not in seen:
                seen.add(key)
                results.append({
                    "type": "malware",
                    "value": word,
                    "raw_value": raw,
                    "canonical_value": None,
                })

        # Check for tools
        if word_lower in tools:
            key = ("tool", word_lower)
            if key not in seen:
                seen.add(key)
                results.append({
                    "type": "tool",
                    "value": word,
                    "raw_value": raw,
                    "canonical_value": None,
                })

    return results


def extract_words_and_phrases(content: str) -> List[tuple]:
    """
    Extract words and multi-word phrases from content.

    Returns list of (normalized, raw) tuples.
    """
    results = []

    # Single words
    word_pattern = re.compile(r'\b[A-Za-z][A-Za-z0-9_-]*[A-Za-z0-9]\b|\b[A-Za-z]\b')
    for match in word_pattern.finditer(content):
        word = match.group()
        results.append((word, word))

    # Two-word phrases (for names like "Forest Blizzard", "Cobalt Strike")
    two_word_pattern = re.compile(r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b')
    for match in two_word_pattern.finditer(content):
        phrase = f"{match.group(1)} {match.group(2)}"
        results.append((phrase, phrase))

    # APT patterns (APT28, APT-28, etc.)
    apt_pattern = re.compile(r'\bAPT[-]?\d+\b', re.IGNORECASE)
    for match in apt_pattern.finditer(content):
        apt = match.group()
        # Normalize: APT28 format
        normalized = re.sub(r'APT[-]?(\d+)', r'APT\1', apt, flags=re.IGNORECASE).upper()
        results.append((normalized, apt))

    # UNC patterns (UNC2452, etc.)
    unc_pattern = re.compile(r'\bUNC\d+\b', re.IGNORECASE)
    for match in unc_pattern.finditer(content):
        results.append((match.group().upper(), match.group()))

    # FIN patterns (FIN7, FIN12, etc.)
    fin_pattern = re.compile(r'\bFIN\d+\b', re.IGNORECASE)
    for match in fin_pattern.finditer(content):
        results.append((match.group().upper(), match.group()))

    return results

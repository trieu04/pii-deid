import re
from dataclasses import dataclass

from src.models import EntityType


@dataclass
class RegexDetector:
    pattern: str
    entity_type: EntityType
    confidence: float = 1.0


_DETECTORS: list[RegexDetector] = [
    # Vietnamese phone numbers: 09x, 03x, +84, 84 prefixes
    RegexDetector(
        r"(\+84|84|0)(3[2-9]|5[2689]|7[06-9]|8[1-9]|9[0-9])[0-9]{7,8}",
        EntityType.PHONE,
        confidence=0.95,
    ),
    # CCCD: 9 or 12 digits — require NOT preceded by a digit (avoids matching
    # inside treatmentCodes, timestamps, etc.)
    RegexDetector(r"(?<!\d)\d{9}(?!\d)|(?<!\d)\d{12}(?!\d)", EntityType.CCCD, confidence=0.7),
    # Email
    RegexDetector(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
        EntityType.EMAIL,
        confidence=1.0,
    ),
    # HEIN card: 2 uppercase letters + 10-13 digits (BHYT pattern)
    RegexDetector(r"\b[A-Z]{2}\d{10,13}\b", EntityType.HEIN_CARD, confidence=0.9),
    # Date of birth: DD/MM/YYYY
    RegexDetector(r"\b\d{1,2}/\d{1,2}/\d{4}\b", EntityType.DOB, confidence=0.95),
    # Year: standalone 4-digit year, not part of a date (not preceded by / or digit)
    RegexDetector(r"(?<![/0-9])(19|20)\d{2}(?![/0-9])", EntityType.DOB_YEAR, confidence=0.5),
]


def detect_regex(text: str) -> list:
    results = []
    for detector in _DETECTORS:
        for match in re.finditer(detector.pattern, text):
            results.append(
                {
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "type": detector.entity_type,
                    "confidence": detector.confidence,
                    "source": "regex",
                }
            )
    return results

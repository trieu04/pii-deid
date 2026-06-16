from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EntityType(str, Enum):
    FULL_NAME = "FULL_NAME"
    PHONE = "PHONE"
    CCCD = "CCCD"
    EMAIL = "EMAIL"
    ADDRESS = "ADDRESS"
    DOB = "DOB"
    DOB_YEAR = "DOB_YEAR"
    ID_NUMBER = "ID_NUMBER"
    HEIN_CARD = "HEIN_CARD"
    BLOOD_TYPE = "BLOOD_TYPE"
    GENDER = "GENDER"
    AGE = "AGE"
    PERSON_RELATIVE = "PERSON_RELATIVE"
    INTERNAL_ID = "INTERNAL_ID"
    FREE_TEXT = "FREE_TEXT"


@dataclass
class PIIEntity:
    text: str
    entity_type: EntityType
    start: int
    end: int
    confidence: float = 1.0
    source: str = "regex"


@dataclass
class ProcessingStats:
    entities_found: int = 0
    processing_ms: float = 0.0

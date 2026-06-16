from src.models import EntityType, PIIEntity
from src.detection.regex_rules import detect_regex
from src.detection.ner_engine import detect_ner


def detect_all(text: str, ner_enabled: bool = True, ner_min_confidence: float = 0.6) -> list[PIIEntity]:
    """
    Combine regex + NER results, deduplicate overlapping spans.
    Regex always wins over NER for overlapping regions.
    """
    if not text or not isinstance(text, str):
        return []

    raw: list[dict] = []
    raw.extend(detect_regex(text))

    if ner_enabled:
        raw.extend(detect_ner(text, min_confidence=ner_min_confidence))

    # Sort by start, then by length descending (longer = more specific)
    raw.sort(key=lambda x: (x["start"], -(x["end"] - x["start"])))

    # Deduplicate overlapping spans: regex wins
    merged: list[PIIEntity] = []
    for item in raw:
        span = (item["start"], item["end"])
        overlaps = False
        for existing in merged:
            # Check overlap
            if not (span[1] <= existing.start or span[0] >= existing.end):
                # If existing is regex and current is ner, skip current
                if existing.source == "regex" and item["source"] == "ner":
                    overlaps = True
                    break
                # If current is regex and existing is ner, remove existing
                elif item["source"] == "regex" and existing.source == "ner":
                    merged.remove(existing)
                    break

        if not overlaps:
            merged.append(
                PIIEntity(
                    text=item["text"],
                    entity_type=item["type"],
                    start=item["start"],
                    end=item["end"],
                    confidence=item["confidence"],
                    source=item["source"],
                )
            )

    return merged

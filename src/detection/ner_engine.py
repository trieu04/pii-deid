from src.models import EntityType


def detect_ner(text: str, min_confidence: float = 0.6) -> list:
    """
    Uses underthesea NER on Vietnamese text.
    Accumulates BIO-tagged tokens into full entity spans before returning.
    Maps: PER -> FULL_NAME, LOC -> ADDRESS, ORG -> FULL_NAME.
    """
    try:
        import underthesea
    except ImportError:
        return []

    try:
        tagged = underthesea.ner(text)
    except Exception:
        return []

    entities = []
    pos = 0

    while pos < len(text):
        # Skip non-word characters
        while pos < len(text) and not text[pos].isalnum():
            pos += 1
        if pos >= len(text):
            break

        remaining = text[pos:]

        # Try to match any tagged token at this position
        matched = False
        for token, tag in tagged:
            if remaining.startswith(token):
                if tag in ("B-PER", "I-PER", "E-PER", "S-PER"):
                    entity_type = EntityType.FULL_NAME
                elif tag in ("B-LOC", "I-LOC", "E-LOC", "S-LOC"):
                    entity_type = EntityType.ADDRESS
                elif tag in ("B-ORG", "I-ORG", "E-ORG", "S-ORG"):
                    entity_type = EntityType.FULL_NAME
                else:
                    continue

                entities.append(
                    {
                        "text": token,
                        "start": pos,
                        "end": pos + len(token),
                        "type": entity_type,
                        "confidence": 0.75,
                        "source": "ner",
                    }
                )
                pos += len(token)
                matched = True
                break

        if not matched:
            pos += 1

    return entities

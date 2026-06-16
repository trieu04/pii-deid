import time
from typing import Any

from src.config import Config
from src.detection.engine import detect_all
from src.models import EntityType, ProcessingStats
from src.pseudonym.mapper import get_pseudonym


def deidentify_json(data: Any, config: Config) -> tuple[Any, ProcessingStats]:
    stats = ProcessingStats()
    start = time.perf_counter()

    result = _walk(data, config, stats, depth=0)

    stats.processing_ms = (time.perf_counter() - start) * 1000
    return result, stats


def _walk(
    data: Any, config: Config, stats: ProcessingStats, depth: int
) -> Any:
    if depth > config.max_depth:
        return data

    if isinstance(data, dict):
        return _process_dict(data, config, stats, depth)
    elif isinstance(data, list):
        return [_walk(item, config, stats, depth + 1) for item in data]
    else:
        return data


def _process_dict(
    obj: dict, config: Config, stats: ProcessingStats, depth: int
) -> dict:
    result = {}
    for key, value in obj.items():
        mapped_type = config.field_mapping.get(key)

        if mapped_type is None:
            result[key] = _walk(value, config, stats, depth + 1)
            continue

        if mapped_type == "FREE_TEXT":
            result[key] = _deidentify_free_text(value, config, stats)
        elif mapped_type == "INTERNAL_ID":
            result[key] = value
        elif mapped_type in [e.value for e in EntityType]:
            result[key] = _deidentify_structured(value, EntityType(mapped_type), config, stats)
        else:
            result[key] = _walk(value, config, stats, depth + 1)

    return result


def _deidentify_free_text(
    text: Any, config: Config, stats: ProcessingStats
) -> Any:
    if not isinstance(text, str):
        return text

    entities = detect_all(text, ner_enabled=config.ner_enabled, ner_min_confidence=config.ner_min_confidence)
    stats.entities_found += len(entities)

    if not entities:
        return text

    # Sort descending by start to avoid offset shifts during replacement
    entities.sort(key=lambda e: e.start, reverse=True)

    for entity in entities:
        pseudonym = get_pseudonym(entity.entity_type, entity.text, config.salt)
        text = text[: entity.start] + pseudonym + text[entity.end :]

    return text


def _deidentify_structured(
    value: Any, entity_type: EntityType, config: Config, stats: ProcessingStats
) -> Any:
    if value is None or value == "":
        return value
    stats.entities_found += 1
    return get_pseudonym(entity_type, str(value), config.salt)

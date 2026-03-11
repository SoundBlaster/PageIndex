from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any, Iterable

from .retrieval_schema import RetrievalDocument

DEFAULT_TOP_K = 7
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True, slots=True)
class CandidateSelectionResult:
    query: str
    top_k: int
    total_records: int
    selected_documents: list[RetrievalDocument]


def load_catalog_payload(catalog: str | Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(catalog, dict):
        return catalog
    return json.loads(Path(catalog).expanduser().resolve().read_text(encoding="utf-8"))


def select_candidate_documents(
    query: str,
    catalog: str | Path | dict[str, Any],
    *,
    top_k: int = DEFAULT_TOP_K,
    document_types: Iterable[str] | None = None,
    path_prefix: str | None = None,
    include_default_excluded: bool = False,
) -> list[RetrievalDocument]:
    payload = load_catalog_payload(catalog)
    requested_types = {value.strip().lower() for value in document_types or [] if value.strip()}
    normalized_path_prefix = _normalize_path_prefix(path_prefix)
    query_tokens = _tokenize(query)

    ranked_candidates: list[tuple[tuple[Any, ...], RetrievalDocument]] = []
    for record in payload.get("records", []):
        if not _record_matches_filters(
            record,
            requested_types=requested_types,
            normalized_path_prefix=normalized_path_prefix,
            include_default_excluded=include_default_excluded,
        ):
            continue

        lexical_score = _lexical_score(record, query, query_tokens)
        if query_tokens and lexical_score <= 0:
            continue

        freshness_timestamp = record.get("ranking_signals", {}).get("freshness_timestamp")
        ranking_score = _ranking_score(record, lexical_score, freshness_timestamp)
        ranked_candidates.append(
            (
                _sort_key(record, lexical_score, freshness_timestamp),
                _record_to_retrieval_document(record, ranking_score=ranking_score),
            )
        )

    ranked_candidates.sort(key=lambda item: item[0])
    return [document for _, document in ranked_candidates[:top_k]]


def _record_matches_filters(
    record: dict[str, Any],
    *,
    requested_types: set[str],
    normalized_path_prefix: str | None,
    include_default_excluded: bool,
) -> bool:
    document_type = str(record.get("document_type", "")).lower()
    if requested_types and document_type not in requested_types:
        return False

    if (
        not include_default_excluded
        and not requested_types
        and record.get("ranking_signals", {}).get("default_excluded") is True
    ):
        return False

    source_rel_path = str(record.get("source_rel_path", "")).lower()
    relative_directory = str(record.get("relative_directory", "")).lower()
    if normalized_path_prefix and not (
        source_rel_path.startswith(normalized_path_prefix)
        or relative_directory.startswith(normalized_path_prefix.rstrip("/"))
    ):
        return False
    return True


def _lexical_score(record: dict[str, Any], query: str, query_tokens: set[str]) -> float:
    if not query_tokens:
        return 1.0

    document_name = str(record.get("document_name", ""))
    source_rel_path = str(record.get("source_rel_path", ""))
    relative_directory = str(record.get("relative_directory", ""))

    score = 0.0
    if _contains_phrase(document_name, query):
        score += 6.0
    if _contains_phrase(source_rel_path, query):
        score += 4.0
    if _contains_phrase(relative_directory, query):
        score += 2.0

    score += _weighted_token_overlap(query_tokens, _tokenize(document_name), 3.0)
    score += _weighted_token_overlap(query_tokens, _tokenize(source_rel_path), 2.0)
    score += _weighted_token_overlap(query_tokens, _tokenize(relative_directory), 1.0)
    return score


def _weighted_token_overlap(query_tokens: set[str], candidate_tokens: set[str], weight: float) -> float:
    if not query_tokens or not candidate_tokens:
        return 0.0
    overlap = len(query_tokens & candidate_tokens)
    return (overlap / len(query_tokens)) * weight


def _contains_phrase(candidate: str, query: str) -> bool:
    normalized_candidate = _normalize_text(candidate)
    normalized_query = _normalize_text(query)
    return bool(normalized_candidate and normalized_query and normalized_query in normalized_candidate)


def _ranking_score(
    record: dict[str, Any],
    lexical_score: float,
    freshness_timestamp: str | None,
) -> float:
    type_priority = int(record.get("ranking_signals", {}).get("type_priority", 99))
    type_boost = max(0, 100 - type_priority)
    freshness_boost = _freshness_sort_value(freshness_timestamp) / 1_000_000_000_000
    return round(lexical_score + type_boost + freshness_boost, 6)


def _sort_key(
    record: dict[str, Any],
    lexical_score: float,
    freshness_timestamp: str | None,
) -> tuple[Any, ...]:
    ranking_signals = record.get("ranking_signals", {})
    return (
        -lexical_score,
        int(ranking_signals.get("type_priority", 99)),
        -_freshness_sort_value(freshness_timestamp),
        str(record.get("source_rel_path", "")),
        str(record.get("record_id", "")),
    )


def _freshness_sort_value(timestamp: str | None) -> int:
    if not timestamp:
        return 0

    normalized_timestamp = timestamp.replace("Z", "+00:00")
    try:
        return int(datetime.fromisoformat(normalized_timestamp).timestamp())
    except ValueError:
        try:
            return int(datetime.fromisoformat(f"{timestamp}T00:00:00").timestamp())
        except ValueError:
            return 0


def _record_to_retrieval_document(
    record: dict[str, Any],
    *,
    ranking_score: float,
) -> RetrievalDocument:
    return RetrievalDocument(
        record_id=str(record["record_id"]),
        document_name=str(record["document_name"]),
        document_type=str(record["document_type"]),
        source_path=str(record["source_path"]),
        output_path=str(record["output_path"]),
        source_rel_path=str(record["source_rel_path"]),
        output_rel_path=str(record["output_rel_path"]),
        freshness_timestamp=record.get("ranking_signals", {}).get("freshness_timestamp"),
        ranking_score=ranking_score,
    )


def _normalize_path_prefix(path_prefix: str | None) -> str | None:
    if path_prefix is None:
        return None
    normalized = str(path_prefix).strip().replace("\\", "/").lower().strip("/")
    if not normalized:
        return None
    return f"{normalized}/"


def _tokenize(value: str) -> set[str]:
    normalized = _normalize_text(value)
    return {match.group(0) for match in _TOKEN_PATTERN.finditer(normalized.lower())}


def _normalize_text(value: str) -> str:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    normalized = normalized.replace("_", " ").replace("-", " ").replace("/", " ")
    normalized = " ".join(normalized.lower().split())
    return normalized

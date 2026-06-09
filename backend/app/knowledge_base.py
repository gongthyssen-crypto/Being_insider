from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import math
import os
from pathlib import Path
import re

import httpx

from app.schemas import ScenarioSeed, SessionState, TurnLog

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_INDEX_ROOT = PROJECT_ROOT / ".knowledge_index"
KNOWLEDGE_INDEX_VERSION = 1
KNOWLEDGE_RETRIEVAL_MODE = os.getenv("KNOWLEDGE_RETRIEVAL_MODE", "auto").strip().lower() or "auto"
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "").strip()
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "").strip()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "").strip()
EMBEDDING_TIMEOUT_SECONDS = float(os.getenv("EMBEDDING_TIMEOUT_SECONDS", "60"))
EMBEDDING_BATCH_SIZE = max(1, int(os.getenv("EMBEDDING_BATCH_SIZE", "16")))
KNOWLEDGE_CHUNK_SIZE = max(300, int(os.getenv("KNOWLEDGE_CHUNK_SIZE", "900")))
KNOWLEDGE_CHUNK_OVERLAP = max(50, int(os.getenv("KNOWLEDGE_CHUNK_OVERLAP", "120")))

SCENARIO_KNOWLEDGE_DIRS: dict[str, Path] = {
    "yuan_shikai_korea": PROJECT_ROOT / "scenario_1",
    "zhang_juzheng_reform": PROJECT_ROOT / "scenario_2",
    "li_quan_red_turban": PROJECT_ROOT / "scenario_3",
}


@dataclass(frozen=True)
class KnowledgeDocument:
    source_name: str
    title: str
    content: str
    terms: frozenset[str]


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    source_name: str
    title: str
    content: str


@dataclass(frozen=True)
class EmbeddedChunk:
    chunk_id: str
    source_name: str
    title: str
    content: str
    embedding: tuple[float, ...]


@dataclass(frozen=True)
class KnowledgeMatch:
    source_name: str
    title: str
    excerpt: str
    score: float


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_title(markdown_text: str, fallback_name: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback_name


def _extract_terms(text: str) -> frozenset[str]:
    ascii_terms = {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9_]{3,}", text)
    }
    cjk_terms: set[str] = set()
    for fragment in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        if len(fragment) <= 8:
            cjk_terms.add(fragment)
        for window in (2, 3):
            if len(fragment) < window:
                continue
            for index in range(len(fragment) - window + 1):
                cjk_terms.add(fragment[index:index + window])
    return frozenset(ascii_terms | cjk_terms)


def _scenario_markdown_paths(scenario_id: str) -> list[Path]:
    directory = SCENARIO_KNOWLEDGE_DIRS.get(scenario_id)
    if directory is None or not directory.exists():
        return []
    return sorted(directory.glob("*.md"))


def _load_scenario_documents(scenario_id: str) -> tuple[KnowledgeDocument, ...]:
    documents: list[KnowledgeDocument] = []
    for path in _scenario_markdown_paths(scenario_id):
        raw_text = path.read_text(encoding="utf-8-sig")
        title = _extract_title(raw_text, path.stem)
        normalized = _normalize_text(raw_text)
        documents.append(
            KnowledgeDocument(
                source_name=path.name,
                title=title,
                content=normalized,
                terms=_extract_terms(f"{title}\n{normalized}"),
            )
        )
    return tuple(documents)


def _source_signature(scenario_id: str) -> list[dict[str, int | str]]:
    return [
        {
            "name": path.name,
            "size": path.stat().st_size,
            "mtime_ns": path.stat().st_mtime_ns,
        }
        for path in _scenario_markdown_paths(scenario_id)
    ]


def _chunk_text(text: str, *, max_chars: int, overlap_chars: int) -> list[str]:
    normalized = _normalize_text(text)
    if not normalized:
        return []

    chunks: list[str] = []
    cursor = 0
    text_length = len(normalized)

    while cursor < text_length:
        end = min(text_length, cursor + max_chars)
        if end < text_length:
            split_window_start = max(cursor, end - 120)
            split_index = -1
            for marker in ("。", "！", "？", ".", ";", "；", ",", "，", " "):
                candidate = normalized.rfind(marker, split_window_start, end)
                split_index = max(split_index, candidate)
            if split_index > cursor + 80:
                end = split_index + 1

        chunk = normalized[cursor:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break
        cursor = max(cursor + 1, end - overlap_chars)

    return chunks


def _document_chunks(document: KnowledgeDocument) -> list[KnowledgeChunk]:
    chunks = _chunk_text(
        document.content,
        max_chars=KNOWLEDGE_CHUNK_SIZE,
        overlap_chars=KNOWLEDGE_CHUNK_OVERLAP,
    )
    if not chunks:
        return []

    return [
        KnowledgeChunk(
            chunk_id=f"{document.source_name}::chunk::{index}",
            source_name=document.source_name,
            title=document.title,
            content=chunk,
        )
        for index, chunk in enumerate(chunks, start=1)
    ]


def list_knowledge_sources(scenario_id: str) -> list[str]:
    return [document.source_name for document in _load_scenario_documents(scenario_id)]


def embedding_index_path(scenario_id: str) -> Path:
    return KNOWLEDGE_INDEX_ROOT / f"{scenario_id}.json"


def is_embedding_configured() -> bool:
    return bool(EMBEDDING_BASE_URL and EMBEDDING_MODEL)


def current_knowledge_retrieval_mode() -> str:
    if KNOWLEDGE_RETRIEVAL_MODE == "keyword":
        return "keyword"
    if KNOWLEDGE_RETRIEVAL_MODE == "embedding" and is_embedding_configured():
        return f"embedding:{EMBEDDING_MODEL}"
    if KNOWLEDGE_RETRIEVAL_MODE == "embedding":
        return "keyword-fallback:embedding-config-missing"
    if is_embedding_configured():
        return f"embedding:{EMBEDDING_MODEL}"
    return "keyword"


def _embedding_endpoint() -> str:
    if EMBEDDING_BASE_URL.endswith("/embeddings"):
        return EMBEDDING_BASE_URL
    return f"{EMBEDDING_BASE_URL.rstrip('/')}/embeddings"


def _normalize_vector(values: list[float]) -> tuple[float, ...]:
    magnitude = math.sqrt(sum(value * value for value in values))
    if magnitude == 0:
        raise ValueError("Embedding vector magnitude is zero")
    return tuple(value / magnitude for value in values)


def _request_embeddings(texts: list[str]) -> list[tuple[float, ...]]:
    if not is_embedding_configured():
        raise RuntimeError("Embedding service is not configured")

    headers = {"Content-Type": "application/json"}
    if EMBEDDING_API_KEY:
        headers["Authorization"] = f"Bearer {EMBEDDING_API_KEY}"

    payload = {
        "model": EMBEDDING_MODEL,
        "input": texts,
    }

    with httpx.Client(timeout=EMBEDDING_TIMEOUT_SECONDS) as client:
        response = client.post(_embedding_endpoint(), headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    items = data.get("data")
    if not isinstance(items, list) or len(items) != len(texts):
        raise ValueError("Embedding response data is missing or has unexpected length")

    normalized_vectors: list[tuple[float, ...]] = []
    for item in items:
        embedding = item.get("embedding") if isinstance(item, dict) else None
        if not isinstance(embedding, list) or not embedding:
            raise ValueError("Embedding item is missing vector data")
        normalized_vectors.append(_normalize_vector([float(value) for value in embedding]))
    return normalized_vectors


def _build_embedded_chunks(scenario_id: str) -> list[EmbeddedChunk]:
    documents = _load_scenario_documents(scenario_id)
    chunks: list[KnowledgeChunk] = []
    for document in documents:
        chunks.extend(_document_chunks(document))

    if not chunks:
        return []

    embeddings: list[tuple[float, ...]] = []
    for offset in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
        batch = chunks[offset:offset + EMBEDDING_BATCH_SIZE]
        embeddings.extend(_request_embeddings([chunk.content for chunk in batch]))

    return [
        EmbeddedChunk(
            chunk_id=chunk.chunk_id,
            source_name=chunk.source_name,
            title=chunk.title,
            content=chunk.content,
            embedding=embedding,
        )
        for chunk, embedding in zip(chunks, embeddings, strict=True)
    ]


def _index_manifest(scenario_id: str) -> dict[str, object]:
    return {
        "version": KNOWLEDGE_INDEX_VERSION,
        "scenario_id": scenario_id,
        "embedding_model": EMBEDDING_MODEL,
        "chunk_size": KNOWLEDGE_CHUNK_SIZE,
        "chunk_overlap": KNOWLEDGE_CHUNK_OVERLAP,
        "source_signature": _source_signature(scenario_id),
    }


def _write_index_file(scenario_id: str, chunks: list[EmbeddedChunk]) -> Path:
    KNOWLEDGE_INDEX_ROOT.mkdir(parents=True, exist_ok=True)
    index_path = embedding_index_path(scenario_id)
    payload = {
        "manifest": _index_manifest(scenario_id),
        "chunks": [
            {
                "chunk_id": chunk.chunk_id,
                "source_name": chunk.source_name,
                "title": chunk.title,
                "content": chunk.content,
                "embedding": list(chunk.embedding),
            }
            for chunk in chunks
        ],
    }
    index_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return index_path


def build_scenario_embedding_index(scenario_id: str, *, force: bool = False) -> Path:
    if scenario_id not in SCENARIO_KNOWLEDGE_DIRS:
        raise KeyError(f"Unknown scenario id: {scenario_id}")
    if not is_embedding_configured():
        raise RuntimeError("Embedding service is not configured")

    index_path = embedding_index_path(scenario_id)
    if not force and _index_is_current(scenario_id):
        return index_path

    chunks = _build_embedded_chunks(scenario_id)
    return _write_index_file(scenario_id, chunks)


def build_all_embedding_indexes(*, force: bool = False) -> list[Path]:
    return [
        build_scenario_embedding_index(scenario_id, force=force)
        for scenario_id in SCENARIO_KNOWLEDGE_DIRS
    ]


def _load_embedding_index(scenario_id: str) -> tuple[dict[str, object], list[EmbeddedChunk]]:
    index_path = embedding_index_path(scenario_id)
    if not index_path.exists():
        return {}, []

    payload = json.loads(index_path.read_text(encoding="utf-8"))
    manifest = payload.get("manifest")
    chunk_items = payload.get("chunks")
    if not isinstance(manifest, dict) or not isinstance(chunk_items, list):
        return {}, []

    chunks: list[EmbeddedChunk] = []
    for item in chunk_items:
        if not isinstance(item, dict):
            continue
        try:
            chunks.append(
                EmbeddedChunk(
                    chunk_id=str(item["chunk_id"]),
                    source_name=str(item["source_name"]),
                    title=str(item["title"]),
                    content=str(item["content"]),
                    embedding=tuple(float(value) for value in item["embedding"]),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue

    return manifest, chunks


def _index_is_current(scenario_id: str) -> bool:
    manifest, chunks = _load_embedding_index(scenario_id)
    if not manifest or not chunks:
        return False

    expected_manifest = _index_manifest(scenario_id)
    return manifest == expected_manifest


def _ensure_embedding_index(scenario_id: str) -> list[EmbeddedChunk]:
    if not is_embedding_configured():
        return []

    if not _index_is_current(scenario_id):
        build_scenario_embedding_index(scenario_id, force=True)

    _, chunks = _load_embedding_index(scenario_id)
    return chunks


def _keyword_matches(
    scenario_id: str,
    query: str,
    *,
    max_matches: int,
    max_excerpt_chars: int,
) -> list[KnowledgeMatch]:
    documents = _load_scenario_documents(scenario_id)
    if not documents:
        return []

    query_terms = _extract_terms(query)
    scored: list[tuple[int, KnowledgeDocument]] = []
    for document in documents:
        overlap = len(query_terms & document.terms)
        title_bonus = 2 * len(query_terms & _extract_terms(document.title))
        score = overlap + title_bonus
        if score > 0:
            scored.append((score, document))

    if not scored:
        scored = [(1, document) for document in documents[:max_matches]]

    scored.sort(key=lambda item: (-item[0], item[1].source_name))
    return [
        KnowledgeMatch(
            source_name=document.source_name,
            title=document.title,
            excerpt=_truncate_excerpt(document.content, max_excerpt_chars),
            score=float(score),
        )
        for score, document in scored[:max_matches]
    ]


def _truncate_excerpt(text: str, max_excerpt_chars: int) -> str:
    excerpt = text[:max_excerpt_chars].rstrip()
    if len(text) > max_excerpt_chars:
        return f"{excerpt}..."
    return excerpt


def _embedding_matches(
    scenario_id: str,
    query: str,
    *,
    max_matches: int,
    max_excerpt_chars: int,
) -> list[KnowledgeMatch]:
    chunks = _ensure_embedding_index(scenario_id)
    if not chunks:
        return []

    query_embedding = _request_embeddings([query])[0]
    scored = [
        (sum(a * b for a, b in zip(query_embedding, chunk.embedding, strict=True)), chunk)
        for chunk in chunks
    ]
    scored.sort(key=lambda item: (-item[0], item[1].chunk_id))

    matches: list[KnowledgeMatch] = []
    seen_chunks: set[str] = set()
    for score, chunk in scored:
        if chunk.chunk_id in seen_chunks:
            continue
        seen_chunks.add(chunk.chunk_id)
        matches.append(
            KnowledgeMatch(
                source_name=chunk.source_name,
                title=chunk.title,
                excerpt=_truncate_excerpt(chunk.content, max_excerpt_chars),
                score=round(score, 4),
            )
        )
        if len(matches) >= max_matches:
            break
    return matches


def retrieve_knowledge_matches(
    scenario_id: str,
    query: str,
    *,
    max_matches: int = 3,
    max_excerpt_chars: int = 900,
) -> list[KnowledgeMatch]:
    mode = KNOWLEDGE_RETRIEVAL_MODE
    should_try_embedding = mode in {"auto", "embedding"}

    if should_try_embedding:
        try:
            matches = _embedding_matches(
                scenario_id,
                query,
                max_matches=max_matches,
                max_excerpt_chars=max_excerpt_chars,
            )
            if matches:
                return matches
        except Exception as exc:
            logger.warning(
                "Embedding retrieval failed for scenario=%s: %s",
                scenario_id,
                exc,
            )
            if mode == "embedding":
                logger.warning("Falling back to keyword retrieval because embedding mode failed.")

    return _keyword_matches(
        scenario_id,
        query,
        max_matches=max_matches,
        max_excerpt_chars=max_excerpt_chars,
    )


def build_turn_knowledge_briefing(
    seed: ScenarioSeed,
    session: SessionState,
    history: list[TurnLog],
    action_text: str,
) -> str:
    query_parts = [
        seed.title,
        seed.player_role,
        seed.historical_anchor,
        seed.primary_goal,
        session.world_summary.situation,
        " ".join(session.world_summary.pressure_points),
        action_text,
    ]

    if history:
        latest_turn = history[-1]
        query_parts.extend(
            [
                latest_turn.player_action,
                latest_turn.outcome_summary,
                latest_turn.world_update,
            ]
        )

    matches = retrieve_knowledge_matches(seed.id, "\n".join(query_parts))
    if not matches:
        return ""

    sections = []
    for index, match in enumerate(matches, start=1):
        sections.append(
            "\n".join(
                [
                    f"[Reference {index}] {match.title}",
                    f"Source: {match.source_name}",
                    f"Relevance score: {match.score}",
                    match.excerpt,
                ]
            )
        )

    return (
        "Supplemental historical references for this turn are provided below. "
        "Use them when they are relevant, prefer them over vague generalities, "
        "and do not quote them verbatim.\n\n"
        + "\n\n".join(sections)
    )

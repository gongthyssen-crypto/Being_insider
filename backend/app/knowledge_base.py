from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re

from app.schemas import ScenarioSeed, SessionState, TurnLog

PROJECT_ROOT = Path(__file__).resolve().parents[2]

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
class KnowledgeMatch:
    source_name: str
    title: str
    excerpt: str
    score: int


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


@lru_cache(maxsize=None)
def _load_scenario_documents(scenario_id: str) -> tuple[KnowledgeDocument, ...]:
    directory = SCENARIO_KNOWLEDGE_DIRS.get(scenario_id)
    if directory is None or not directory.exists():
        return ()

    documents: list[KnowledgeDocument] = []
    for path in sorted(directory.glob("*.md")):
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


def list_knowledge_sources(scenario_id: str) -> list[str]:
    return [document.source_name for document in _load_scenario_documents(scenario_id)]


def retrieve_knowledge_matches(
    scenario_id: str,
    query: str,
    *,
    max_matches: int = 3,
    max_excerpt_chars: int = 900,
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
    matches: list[KnowledgeMatch] = []
    for score, document in scored[:max_matches]:
        excerpt = document.content[:max_excerpt_chars].rstrip()
        if len(document.content) > max_excerpt_chars:
            excerpt = f"{excerpt}..."
        matches.append(
            KnowledgeMatch(
                source_name=document.source_name,
                title=document.title,
                excerpt=excerpt,
                score=score,
            )
        )
    return matches


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

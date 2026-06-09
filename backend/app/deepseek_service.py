from __future__ import annotations

import ast
import json
import os
import re
from typing import Any

import httpx

from app.knowledge_base import build_turn_knowledge_briefing
from app.schemas import ScenarioSeed, SessionState, TurnLog

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-2a1d86caf93d4c21ba51be6c69bc7abd")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")


def is_deepseek_configured() -> bool:
    return bool(DEEPSEEK_API_KEY)


def current_model_mode() -> str:
    if is_deepseek_configured():
        return f"deepseek-official:{DEEPSEEK_MODEL}"
    return "seed-session-local-adjudicator-placeholder-key"


def _system_prompt(seed: ScenarioSeed) -> str:
    return f"""
You are the narrative adjudicator for a Chinese ancient-history strategy simulation.
You must reply in valid json.

Scenario title: {seed.title}
Era: {seed.era}
Player role: {seed.player_role}
Historical anchor: {seed.historical_anchor}
Primary goal: {seed.primary_goal}
Failure risk: {seed.failure_risk}

Requirements:
1. Keep the output grounded in the historical setting and role.
2. Treat the player action as a strategic decision in an unfolding situation.
3. Advance the situation by one turn only.
4. Do not write modern slang or meta commentary.
5. Output strict json with this shape:
{{
  "ai_narration": "string",
  "outcome_summary": "string",
  "world_update": "string",
  "next_prompt_hint": "string",
  "suggested_options": [
    {{
      "id": "snake_case_id",
      "label": "string",
      "brief": "string",
      "strategic_hint": "string"
    }}
  ],
  "ending": null
}}
6. Never quote, copy, or closely paraphrase the player's action verbatim. Summarize the action in your own words before judging consequences.
7. Keep "outcome_summary" and "world_update" concise and non-redundant. Do not repeat the same sentence across fields.
8. Do not produce a stage ending before turn 7.
9. Between turn 7 and turn 10, if the situation has clearly reached a stage ending, set "ending" to a concise ending paragraph that explicitly states:
   - what the player has achieved in this stage,
   - what major risk or unresolved cost remains,
   - what direction the situation is likely to move next.
   Otherwise use null.
10. By turn 10, the scenario must be allowed to conclude if the strategic arc has matured.
11. Always provide exactly 3 suggested_options for the player's next turn.
12. Make the 3 suggested_options meaningfully different from each other and responsive to the latest situation.
""".strip()


def _history_messages(history: list[TurnLog]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for turn in history[-6:]:
        messages.append(
            {
                "role": "user",
                "content": f"Previous player action in turn {turn.turn_index}: {turn.player_action}",
            }
        )
        messages.append(
            {
                "role": "assistant",
                "content": json.dumps(
                    {
                        "ai_narration": turn.ai_narration,
                        "outcome_summary": turn.outcome_summary,
                        "world_update": turn.world_update,
                        "next_prompt_hint": "Recorded historical turn",
                        "suggested_options": [],
                        "ending": None,
                    },
                    ensure_ascii=False,
                ),
            }
        )
    return messages


def build_messages(
    seed: ScenarioSeed,
    session: SessionState,
    history: list[TurnLog],
    action_text: str,
) -> list[dict[str, str]]:
    knowledge_briefing = build_turn_knowledge_briefing(
        seed=seed,
        session=session,
        history=history,
        action_text=action_text,
    )
    knowledge_block = ""
    if knowledge_briefing:
        knowledge_block = f"{knowledge_briefing}\n\n"

    messages: list[dict[str, str]] = [{"role": "system", "content": _system_prompt(seed)}]
    messages.extend(_history_messages(history))
    messages.append(
        {
            "role": "user",
            "content": (
                f"Current world summary:\n"
                f"- time_label: {session.world_summary.time_label}\n"
                f"- location: {session.world_summary.location}\n"
                f"- situation: {session.world_summary.situation}\n"
                f"- pressure_points: {'; '.join(session.world_summary.pressure_points)}\n"
                f"- recent_shift: {session.world_summary.recent_shift}\n\n"
                f"{knowledge_block}"
                f"- current_turn: {session.turn_index + 1}\n\n"
                f"Current player action:\n{action_text}\n\n"
                f"Do not quote or repeat the current player action verbatim. Summarize it in your own words.\n"
                f"Return only valid json."
            ),
        }
    )
    return messages


def _strip_markdown_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def _extract_json_object(text: str) -> str | None:
    start = text.find("{")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue
        if char == "{":
            depth += 1
            continue
        if char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    return None


def _escape_control_chars_in_strings(text: str) -> str:
    result: list[str] = []
    in_string = False
    escaped = False

    for char in text:
        if in_string:
            if escaped:
                result.append(char)
                escaped = False
                continue
            if char == "\\":
                result.append(char)
                escaped = True
                continue
            if char == '"':
                result.append(char)
                in_string = False
                continue
            if char == "\n":
                result.append("\\n")
                continue
            if char == "\r":
                result.append("\\r")
                continue
            if char == "\t":
                result.append("\\t")
                continue
            result.append(char)
            continue

        result.append(char)
        if char == '"':
            in_string = True

    return "".join(result)


def _remove_trailing_commas(text: str) -> str:
    return re.sub(r",(\s*[}\]])", r"\1", text)


def _python_literal_fallback(text: str) -> dict[str, Any] | None:
    python_like = re.sub(r"\btrue\b", "True", text)
    python_like = re.sub(r"\bfalse\b", "False", python_like)
    python_like = re.sub(r"\bnull\b", "None", python_like)
    try:
        parsed = ast.literal_eval(python_like)
    except (SyntaxError, ValueError):
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def _parse_json_with_repair(content: str) -> dict[str, Any]:
    candidates: list[str] = []

    def add_candidate(value: str | None) -> None:
        if not value:
            return
        normalized = value.strip()
        if normalized and normalized not in candidates:
            candidates.append(normalized)

    stripped = content.strip()
    add_candidate(stripped)
    add_candidate(_strip_markdown_code_fence(stripped))
    add_candidate(_extract_json_object(stripped))

    for candidate in list(candidates):
        add_candidate(_remove_trailing_commas(candidate))
        add_candidate(_escape_control_chars_in_strings(candidate))
        add_candidate(_remove_trailing_commas(_escape_control_chars_in_strings(candidate)))

    last_error: Exception | None = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            parsed = _python_literal_fallback(candidate)
            if parsed is None:
                continue
        if isinstance(parsed, dict):
            return parsed

    if last_error is not None:
        raise last_error
    raise ValueError("DeepSeek returned content that could not be parsed as JSON")


def request_turn_resolution(
    seed: ScenarioSeed,
    session: SessionState,
    history: list[TurnLog],
    action_text: str,
) -> dict[str, Any] | None:
    if not is_deepseek_configured():
        return None

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": build_messages(seed, session, history, action_text),
        "response_format": {"type": "json_object"},
        "stream": False,
        "max_tokens": 1200,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }

    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    if not content:
        raise ValueError("DeepSeek returned empty content for turn resolution")

    parsed = _parse_json_with_repair(content)
    return {
        "ai_narration": str(parsed.get("ai_narration", "")).strip(),
        "outcome_summary": str(parsed.get("outcome_summary", "")).strip(),
        "world_update": str(parsed.get("world_update", "")).strip(),
        "next_prompt_hint": str(parsed.get("next_prompt_hint", "")).strip(),
        "suggested_options": parsed.get("suggested_options"),
        "ending": parsed.get("ending"),
    }

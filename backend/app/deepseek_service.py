from __future__ import annotations

import json
import os
from typing import Any

import httpx

from app.schemas import ScenarioSeed, SessionState, TurnLog

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
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
                f"- current_turn: {session.turn_index + 1}\n\n"
                f"Current player action:\n{action_text}\n\n"
                f"Do not quote or repeat the current player action verbatim. Summarize it in your own words.\n"
                f"Return only valid json."
            ),
        }
    )
    return messages


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

    parsed = json.loads(content)
    return {
        "ai_narration": str(parsed.get("ai_narration", "")).strip(),
        "outcome_summary": str(parsed.get("outcome_summary", "")).strip(),
        "world_update": str(parsed.get("world_update", "")).strip(),
        "next_prompt_hint": str(parsed.get("next_prompt_hint", "")).strip(),
        "ending": parsed.get("ending"),
    }

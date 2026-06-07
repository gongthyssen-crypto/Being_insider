from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from uuid import uuid4

from app.content import get_scenario_seed
from app.deepseek_service import current_model_mode
from app.schemas import SessionState, TurnLog, WorldSummary


SESSIONS: dict[str, dict] = {}


def _initial_world_summary(seed: dict) -> WorldSummary:
    return WorldSummary(
        time_label=f"{seed['era']} · 开局",
        location=seed["title"],
        situation=seed["opening_situation"],
        pressure_points=[
            seed["primary_goal"],
            seed["failure_risk"],
            seed["historical_anchor"],
        ],
        recent_shift="局势刚刚展开，尚未做出正式决策。",
    )


def create_session(scenario_id: str) -> dict:
    seed = get_scenario_seed(scenario_id)
    now = datetime.now(UTC)
    session_id = str(uuid4())
    session = SessionState(
        session_id=session_id,
        scenario_id=scenario_id,
        status="active",
        turn_index=0,
        created_at=now,
        updated_at=now,
        world_summary=_initial_world_summary(seed),
    )
    SESSIONS[session_id] = {
        "session": session.model_dump(),
        "history": [],
        "latest_narration": seed["opening_situation"],
        "next_prompt_hint": seed["opening_prompt_hint"],
        "runtime_mode": current_model_mode(),
    }
    return deepcopy(SESSIONS[session_id])


def get_session_bundle(session_id: str) -> dict:
    bundle = SESSIONS.get(session_id)
    if bundle is None:
        raise KeyError(session_id)
    return deepcopy(bundle)


def get_session_state(session_id: str) -> SessionState:
    bundle = get_session_bundle(session_id)
    return SessionState(**bundle["session"])


def get_turn_history(session_id: str) -> list[TurnLog]:
    bundle = get_session_bundle(session_id)
    return [TurnLog(**item) for item in bundle["history"]]


def save_turn_result(
    session_id: str,
    session_state: SessionState,
    turn_log: TurnLog,
    latest_narration: str,
    next_prompt_hint: str,
    runtime_mode: str,
) -> dict:
    bundle = SESSIONS.get(session_id)
    if bundle is None:
        raise KeyError(session_id)
    bundle["session"] = session_state.model_dump()
    bundle["history"].append(turn_log.model_dump())
    bundle["latest_narration"] = latest_narration
    bundle["next_prompt_hint"] = next_prompt_hint
    bundle["runtime_mode"] = runtime_mode
    return deepcopy(bundle)

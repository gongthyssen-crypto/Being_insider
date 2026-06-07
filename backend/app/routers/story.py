from __future__ import annotations

from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, HTTPException

from app.content import get_scenario_seed, list_scenarios
from app.deepseek_service import current_model_mode, request_turn_resolution
from app.schemas import (
    CreateSessionRequest,
    HealthPayload,
    PlayerTurnRequest,
    ScenarioCard,
    ScenarioSeed,
    SessionSnapshot,
    SessionState,
    TurnLog,
    TurnResult,
    WorldSummary,
)
from app.session_store import (
    create_session,
    get_session_bundle,
    get_session_state,
    get_turn_history,
    save_turn_result,
)

router = APIRouter(prefix="/api", tags=["story"])
MAX_TURNS = 8


def _seed_payload(scenario_id: str) -> ScenarioSeed:
    return ScenarioSeed(**get_scenario_seed(scenario_id))


def _bundle_to_snapshot(bundle: dict) -> SessionSnapshot:
    session = SessionState(**bundle["session"])
    seed = _seed_payload(session.scenario_id)
    return SessionSnapshot(
        session=session,
        scenario_seed=seed,
        latest_narration=bundle["latest_narration"],
        next_prompt_hint=bundle["next_prompt_hint"],
        runtime_mode=bundle["runtime_mode"],
    )


def _classify_action(action_text: str) -> tuple[str, str]:
    lowered = action_text.lower()
    if any(token in action_text for token in ("安抚", "稳住", "安民", "抚", "谈")):
        return (
            "缓和",
            "你的决定偏向先稳住局面，短期冲突被压低，但后续执行成本还会持续累积。",
        )
    if any(token in action_text for token in ("夺", "攻", "压", "抓", "杀", "调兵")):
        return (
            "强压",
            "你的决定带有明显先手意味，声势会迅速拉高，但也更容易让对手提前警觉。",
        )
    if any(token in action_text for token in ("联络", "结盟", "求援", "上疏", "奏")):
        return (
            "借势",
            "你的决定试图借外力或借制度撬动局面，回旋空间会增加，但依赖与猜疑也会随之出现。",
        )
    if any(token in lowered for token in ("wait", "delay", "observe", "probe")) or any(
        token in action_text for token in ("观察", "试探", "拖", "缓")
    ):
        return (
            "观望",
            "你的决定争取到了判断时间，但主动权并不会因此自动留在你手里。",
        )
    return (
        "调度",
        "你的决定更像一次务实调度，局面不会立刻翻盘，但会逐步显露新的重心与裂缝。",
    )


def _next_time_label(era: str, turn_index: int) -> str:
    return f"{era} · 第 {turn_index} 回合后"


def _build_turn_result(
    session: SessionState,
    seed: ScenarioSeed,
    action_text: str,
    runtime_mode: str = "local-fallback",
) -> TurnResult:
    action_mode, outcome_summary = _classify_action(action_text)
    new_turn_index = session.turn_index + 1
    ai_narration = (
        f"你以“{action_text}”作为本轮决策。{seed.player_role}一方很快感受到这一步的"
        f"{action_mode}意味，周围势力开始重新判断你的底线与能力。"
        f"在 {seed.historical_anchor} 这一历史背景下，这种动作不会只改变眼前局面，"
        "还会重塑他人对你后续路线的预期。"
    )
    world_update = (
        f"围绕“{action_text}”的行动已经让局势出现新偏移：{outcome_summary}"
    )
    next_prompt_hint = (
        "下一轮可以继续写你如何巩固这一决定、修补副作用，或者转向处理新的风险点。"
    )
    ending = None
    status = "active"

    if new_turn_index >= 5:
        status = "ended"
        ending = (
            f"推演暂时走到一个阶段性结局：你围绕“{action_text}”建立了当前路线，"
            "但这条路线能否最终改写历史，还取决于更长期的资源、盟友与节奏控制。"
        )
        next_prompt_hint = "本局已进入阶段性结尾，可以复盘路径或重新开局。"

    updated_world = WorldSummary(
        time_label=_next_time_label(seed.era, new_turn_index),
        location=seed.title,
        situation=(
            f"当前核心任务仍是：{seed.primary_goal}。本轮之后，局势重心转向了"
            f"{action_mode}带来的连锁变化。"
        ),
        pressure_points=[
            seed.failure_risk,
            outcome_summary,
            "需要继续平衡历史背景约束与现实行动空间。",
        ],
        recent_shift=world_update,
    )
    now = datetime.now(UTC)
    updated_session = SessionState(
        session_id=session.session_id,
        scenario_id=session.scenario_id,
        status=status,
        turn_index=new_turn_index,
        created_at=session.created_at,
        updated_at=now,
        world_summary=updated_world,
    )
    turn_log = TurnLog(
        turn_index=new_turn_index,
        player_action=action_text,
        ai_narration=ai_narration,
        outcome_summary=outcome_summary,
        world_update=world_update,
        resolution_mode=runtime_mode,
        timestamp=now,
    )
    return TurnResult(
        session=updated_session,
        turn=turn_log,
        next_prompt_hint=next_prompt_hint,
        runtime_mode=runtime_mode,
        ending=ending,
    )


def _build_turn_result_from_resolution(
    session: SessionState,
    seed: ScenarioSeed,
    action_text: str,
    resolution: dict,
    runtime_mode: str,
) -> TurnResult:
    new_turn_index = session.turn_index + 1
    ending = resolution.get("ending")
    status = "active"
    next_prompt_hint = resolution.get("next_prompt_hint") or (
        "下一轮继续描述你的行动，说明你准备如何扩大优势或处理新的风险。"
    )

    if new_turn_index >= MAX_TURNS and not ending:
        ending = (
            f"推演进入阶段性结尾：围绕“{action_text}”所展开的路线已经初步成形，"
            "接下来历史会沿着这条路径继续分化，但本局先停在这个阶段。"
        )

    if ending:
        status = "ended"

    ai_narration = resolution.get("ai_narration") or (
        f"你以“{action_text}”作为本轮决策，局势随即出现新的震动。"
    )
    outcome_summary = resolution.get("outcome_summary") or (
        "这一决策已经改变了局势平衡，但新的后果仍在继续显现。"
    )
    world_update = resolution.get("world_update") or outcome_summary

    updated_world = WorldSummary(
        time_label=_next_time_label(seed.era, new_turn_index),
        location=seed.title,
        situation=(
            f"当前核心任务仍是：{seed.primary_goal}。本轮之后，局势围绕你的行动"
            "继续向新的方向偏移。"
        ),
        pressure_points=[
            seed.failure_risk,
            outcome_summary,
            "需要继续平衡历史背景约束与现实行动空间。",
        ],
        recent_shift=world_update,
    )
    now = datetime.now(UTC)
    updated_session = SessionState(
        session_id=session.session_id,
        scenario_id=session.scenario_id,
        status=status,
        turn_index=new_turn_index,
        created_at=session.created_at,
        updated_at=now,
        world_summary=updated_world,
    )
    turn_log = TurnLog(
        turn_index=new_turn_index,
        player_action=action_text,
        ai_narration=ai_narration,
        outcome_summary=outcome_summary,
        world_update=world_update,
        resolution_mode=runtime_mode,
        timestamp=now,
    )
    return TurnResult(
        session=updated_session,
        turn=turn_log,
        next_prompt_hint=next_prompt_hint,
        runtime_mode=runtime_mode,
        ending=ending,
    )


@router.get("/health", response_model=HealthPayload)
def health() -> HealthPayload:
    return HealthPayload(
        status="ok",
        api_name="ai-history-sandbox",
        model_mode=current_model_mode(),
    )


@router.get("/scenarios", response_model=list[ScenarioCard])
def scenarios() -> list[ScenarioCard]:
    return [ScenarioCard(**item) for item in list_scenarios()]


@router.get("/scenarios/{scenario_id}", response_model=ScenarioSeed)
def scenario_seed(scenario_id: str) -> ScenarioSeed:
    try:
        return _seed_payload(scenario_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Scenario not found") from exc


@router.post("/sessions", response_model=SessionSnapshot)
def create_story_session(payload: CreateSessionRequest) -> SessionSnapshot:
    try:
        bundle = create_session(payload.scenario_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Scenario not found") from exc
    return _bundle_to_snapshot(bundle)


@router.get("/sessions/{session_id}", response_model=SessionSnapshot)
def get_story_session(session_id: str) -> SessionSnapshot:
    try:
        bundle = get_session_bundle(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    return _bundle_to_snapshot(bundle)


@router.get("/sessions/{session_id}/history", response_model=list[TurnLog])
def session_history(session_id: str) -> list[TurnLog]:
    try:
        return get_turn_history(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc


@router.post("/sessions/{session_id}/turns", response_model=TurnResult)
def submit_turn(session_id: str, payload: PlayerTurnRequest) -> TurnResult:
    try:
        session = get_session_state(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc

    if session.status == "ended":
        raise HTTPException(status_code=400, detail="Session already ended")

    try:
        seed = _seed_payload(session.scenario_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Scenario not found") from exc

    action_text = payload.action_text.strip()
    if not action_text:
        raise HTTPException(status_code=400, detail="Action text cannot be empty")

    if payload.source_option_id:
        matched = next(
            (item for item in seed.initial_options if item.id == payload.source_option_id),
            None,
        )
        if matched is None:
            raise HTTPException(status_code=400, detail="Opening option not valid")
        action_text = f"{matched.label}：{action_text}"

    history = get_turn_history(session_id)
    runtime_mode = "local-fallback"
    try:
        resolution = request_turn_resolution(seed, session, history, action_text)
        if resolution is not None:
            runtime_mode = current_model_mode()
    except (httpx.HTTPError, ValueError):
        resolution = None
    if resolution is None:
        result = _build_turn_result(session, seed, action_text, runtime_mode=runtime_mode)
    else:
        result = _build_turn_result_from_resolution(
            session,
            seed,
            action_text,
            resolution,
            runtime_mode=runtime_mode,
        )
    save_turn_result(
        session_id,
        result.session,
        result.turn,
        result.turn.ai_narration,
        result.next_prompt_hint,
        result.runtime_mode,
    )
    return result

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ScenarioCard(BaseModel):
    id: str
    title: str
    era: str
    summary: str


class OpeningOption(BaseModel):
    id: str
    label: str
    brief: str
    strategic_hint: str


class ScenarioSeed(BaseModel):
    id: str
    title: str
    era: str
    summary: str
    player_role: str
    opening_situation: str
    historical_anchor: str
    primary_goal: str
    failure_risk: str
    initial_options: list[OpeningOption]
    opening_prompt_hint: str


class WorldSummary(BaseModel):
    time_label: str
    location: str
    situation: str
    pressure_points: list[str]
    recent_shift: str


class SessionState(BaseModel):
    session_id: str
    scenario_id: str
    status: Literal["active", "ended"]
    turn_index: int
    created_at: datetime
    updated_at: datetime
    world_summary: WorldSummary


class StageEnding(BaseModel):
    title: str
    appraisal: str
    route: str
    achievement: str
    risk: str
    outlook: str


class SessionSnapshot(BaseModel):
    session: SessionState
    scenario_seed: ScenarioSeed
    latest_narration: str
    next_prompt_hint: str
    suggested_options: list[OpeningOption]
    runtime_mode: str
    ending: str | None = None
    ending_summary: StageEnding | None = None


class CreateSessionRequest(BaseModel):
    scenario_id: str


class PlayerTurnRequest(BaseModel):
    action_text: str
    source_option_id: str | None = None


class TurnLog(BaseModel):
    turn_index: int
    player_action: str
    ai_narration: str
    outcome_summary: str
    world_update: str
    resolution_mode: str
    timestamp: datetime


class TurnResult(BaseModel):
    session: SessionState
    turn: TurnLog
    next_prompt_hint: str
    suggested_options: list[OpeningOption]
    runtime_mode: str
    ending: str | None = None
    ending_summary: StageEnding | None = None


class HealthPayload(BaseModel):
    status: str
    api_name: str
    model_mode: str
    knowledge_mode: str


class RuntimeSettings(BaseModel):
    deepseek_max_tokens: int
    deepseek_thinking_enabled: bool
    turn_knowledge_max_matches: int
    turn_knowledge_max_excerpt_chars: int


class RuntimeSettingsUpdate(BaseModel):
    deepseek_max_tokens: int | None = None
    deepseek_thinking_enabled: bool | None = None
    turn_knowledge_max_matches: int | None = None
    turn_knowledge_max_excerpt_chars: int | None = None

from __future__ import annotations

import ast
import json
import re
from typing import Any

EXPECTED_RESPONSE_KEYS = (
    "ai_narration",
    "outcome_summary",
    "world_update",
    "next_prompt_hint",
    "suggested_options",
    "ending",
)
REQUIRED_RESPONSE_TEXT_KEYS = EXPECTED_RESPONSE_KEYS[:4]


def strip_markdown_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def extract_json_object(text: str) -> str | None:
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


def slice_outer_braces(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    return text[start:end + 1]


def escape_control_chars_in_strings(text: str) -> str:
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


def remove_trailing_commas(text: str) -> str:
    return re.sub(r",(\s*[}\]])", r"\1", text)


def _python_literal_parse(text: str) -> Any | None:
    python_like = re.sub(r"\btrue\b", "True", text)
    python_like = re.sub(r"\bfalse\b", "False", python_like)
    python_like = re.sub(r"\bnull\b", "None", python_like)
    try:
        return ast.literal_eval(python_like)
    except (SyntaxError, ValueError):
        return None


def python_literal_dict_fallback(text: str) -> dict[str, Any] | None:
    parsed = _python_literal_parse(text)
    if isinstance(parsed, dict):
        return parsed
    return None


def python_literal_list_fallback(text: str) -> list[Any] | None:
    parsed = _python_literal_parse(text)
    if isinstance(parsed, list):
        return parsed
    return None


def decode_relaxed_string_value(raw_value: str) -> str:
    text = raw_value.strip().rstrip(",").strip()
    if not text:
        return ""

    if text[0] in ('"', "'"):
        quote = text[0]
        end_index = text.rfind(quote)
        if end_index > 0:
            text = text[1:end_index]
        else:
            text = text[1:]

    return (
        text.replace("\\r", "\r")
        .replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace('\\"', '"')
        .replace("\\'", "'")
        .replace("\\\\", "\\")
        .strip()
    )


def parse_optional_relaxed_string(raw_value: str) -> str | None:
    normalized = raw_value.strip().rstrip(",").strip()
    if not normalized or normalized in {"null", "None"}:
        return None

    parsed = decode_relaxed_string_value(normalized)
    return parsed or None


def parse_json_list_with_repair(content: str) -> list[Any] | None:
    candidates: list[str] = []

    def add_candidate(value: str | None) -> None:
        if not value:
            return
        normalized = value.strip().rstrip(",").strip()
        if normalized and normalized not in candidates:
            candidates.append(normalized)

    add_candidate(content)
    add_candidate(remove_trailing_commas(content))
    add_candidate(escape_control_chars_in_strings(content))
    add_candidate(remove_trailing_commas(escape_control_chars_in_strings(content)))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            parsed = python_literal_list_fallback(candidate)
        if isinstance(parsed, list):
            return parsed
    return None


def salvage_expected_payload(content: str) -> dict[str, Any] | None:
    stripped = strip_markdown_code_fence(content.strip())
    source = slice_outer_braces(stripped) or stripped
    if not source:
        return None

    positions: list[tuple[str, int, int]] = []
    search_start = 0
    for key in EXPECTED_RESPONSE_KEYS:
        match = re.search(rf'["\']{re.escape(key)}["\']\s*:', source[search_start:])
        if match is None:
            continue
        absolute_start = search_start + match.start()
        absolute_end = search_start + match.end()
        positions.append((key, absolute_start, absolute_end))
        search_start = absolute_end

    found_keys = {key for key, _, _ in positions}
    if any(key not in found_keys for key in REQUIRED_RESPONSE_TEXT_KEYS):
        return None

    payload_end = source.rfind("}")
    if payload_end < 0:
        payload_end = len(source)

    raw_segments: dict[str, str] = {}
    for index, (key, _, value_start) in enumerate(positions):
        value_end = positions[index + 1][1] if index + 1 < len(positions) else payload_end
        raw_segments[key] = source[value_start:value_end]

    salvaged: dict[str, Any] = {}
    for key in REQUIRED_RESPONSE_TEXT_KEYS:
        value = decode_relaxed_string_value(raw_segments.get(key, ""))
        if not value:
            return None
        salvaged[key] = value

    salvaged["suggested_options"] = parse_json_list_with_repair(
        raw_segments.get("suggested_options", "")
    )
    salvaged["ending"] = parse_optional_relaxed_string(raw_segments.get("ending", ""))
    return salvaged


def parse_json_with_repair(content: str) -> dict[str, Any]:
    candidates: list[str] = []

    def add_candidate(value: str | None) -> None:
        if not value:
            return
        normalized = value.strip()
        if normalized and normalized not in candidates:
            candidates.append(normalized)

    stripped = content.strip()
    add_candidate(stripped)
    add_candidate(strip_markdown_code_fence(stripped))
    add_candidate(extract_json_object(stripped))
    add_candidate(slice_outer_braces(stripped))

    for candidate in list(candidates):
        add_candidate(remove_trailing_commas(candidate))
        add_candidate(escape_control_chars_in_strings(candidate))
        add_candidate(remove_trailing_commas(escape_control_chars_in_strings(candidate)))

    last_error: Exception | None = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            parsed = python_literal_dict_fallback(candidate)
            if parsed is None:
                continue
        if isinstance(parsed, dict):
            return parsed

    salvaged = salvage_expected_payload(content)
    if salvaged is not None:
        return salvaged

    if last_error is not None:
        raise last_error
    raise ValueError("Model returned content that could not be parsed as JSON")

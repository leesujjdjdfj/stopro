from __future__ import annotations

import json
import re


class AiProviderError(Exception):
    pass


def clean_env_value(value: str | None) -> str:
    return (value or "").strip().lstrip("\ufeff")


def parse_json_content(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AiProviderError("AI 응답을 JSON으로 해석하지 못했습니다.") from exc
    if not isinstance(parsed, dict):
        raise AiProviderError("AI 응답 형식이 올바르지 않습니다.")
    return parsed

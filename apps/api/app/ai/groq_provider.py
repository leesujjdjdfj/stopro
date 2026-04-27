from __future__ import annotations

import requests

from app.ai.ai_provider import AiProviderError, clean_env_value, parse_json_content


class GroqProvider:
    name = "GROQ"

    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = clean_env_value(api_key)
        self.model = clean_env_value(model)

    def analyze(self, system_prompt: str, user_prompt: str) -> dict:
        if not self.api_key:
            raise AiProviderError("Groq API 키가 설정되지 않았습니다.")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1200,
            "response_format": {"type": "json_object"},
        }
        data = self._post(payload)
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            raise AiProviderError("Groq 응답이 비어 있습니다.")
        return parse_json_content(content)

    def _post(self, payload: dict) -> dict:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=14,
        )
        if response.status_code == 400 and "response_format" in payload:
            payload = {key: value for key, value in payload.items() if key != "response_format"}
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=14,
            )
        if response.status_code >= 400:
            raise AiProviderError(f"Groq 요청 실패: {response.status_code}")
        return response.json()

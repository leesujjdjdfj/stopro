from __future__ import annotations

import requests

from app.ai.ai_provider import AiProviderError, parse_json_content


class OpenRouterProvider:
    name = "OPENROUTER"

    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def analyze(self, system_prompt: str, user_prompt: str) -> dict:
        if not self.api_key:
            raise AiProviderError("OpenRouter API 키가 설정되지 않았습니다.")
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
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://stopro-web.vercel.app",
                "X-Title": "StoPro",
            },
            json=payload,
            timeout=14,
        )
        if response.status_code >= 400:
            raise AiProviderError(f"OpenRouter 요청 실패: {response.status_code}")
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            raise AiProviderError("OpenRouter 응답이 비어 있습니다.")
        return parse_json_content(content)

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class QwenClientError(RuntimeError):
    """Raised when the Qwen-compatible API request fails."""


@dataclass(frozen=True)
class QwenClient:
    api_key: str
    base_url: str
    llm_model: str | None = None
    embedding_model: str | None = None
    timeout_seconds: int = 60
    opener: Callable[..., Any] = urlopen

    def chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1200,
    ) -> str:
        if not self.llm_model:
            raise QwenClientError("LLM model is not configured.")

        payload = {
            "model": self.llm_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = self._post_json("/chat/completions", payload)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise QwenClientError("Unexpected chat completion response format.") from exc

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self.embedding_model:
            raise QwenClientError("Embedding model is not configured.")
        if not texts:
            return []

        payload = {
            "model": self.embedding_model,
            "input": texts,
        }
        data = self._post_json("/embeddings", payload)
        try:
            return [item["embedding"] for item in data["data"]]
        except (KeyError, TypeError) as exc:
            raise QwenClientError("Unexpected embedding response format.") from exc

    def _post_json(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with self.opener(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise QwenClientError(f"Qwen API returned HTTP {exc.code}: {body}") from exc
        except URLError as exc:
            raise QwenClientError(f"Failed to reach Qwen API: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise QwenClientError("Qwen API returned invalid JSON.") from exc


def build_qwen_client(
    *,
    api_key: str | None,
    base_url: str,
    llm_model: str | None,
    embedding_model: str | None,
) -> QwenClient | None:
    if not api_key:
        return None
    return QwenClient(
        api_key=api_key,
        base_url=base_url,
        llm_model=llm_model,
        embedding_model=embedding_model,
    )

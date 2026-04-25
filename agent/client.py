from __future__ import annotations

import json
import ssl
from dataclasses import dataclass
from pathlib import Path
from urllib import error, request

import certifi

from agent.config import Settings
from agent.types import JsonDict


class OpenAICompatibleError(RuntimeError):
    pass


@dataclass(slots=True)
class OpenAICompatibleClient:
    settings: Settings

    def chat_completions(self, messages: list[JsonDict], tools: list[JsonDict]) -> JsonDict:
        if not self.settings.api_key:
            raise OpenAICompatibleError("AI_AGENT_API_KEY не указан")

        payload: JsonDict = {
            "model": self.settings.model,
            "messages": messages,
            "temperature": self.settings.temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        raw_body = json.dumps(payload).encode("utf-8")
        endpoint = f"{self.settings.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.settings.api_key}",
        }
        http_request = request.Request(endpoint, data=raw_body, headers=headers, method="POST")
        ssl_context = self._build_ssl_context()

        try:
            with request.urlopen(http_request, timeout=90, context=ssl_context) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise OpenAICompatibleError(
                f"Upstream API returned HTTP {exc.code}: {details}"
            ) from exc
        except error.URLError as exc:
            raise OpenAICompatibleError(f"Failed to reach API: {exc.reason}") from exc

    def _build_ssl_context(self) -> ssl.SSLContext:
        if not self.settings.ssl_verify:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            return context

        if self.settings.ca_bundle:
            ca_bundle_path = Path(self.settings.ca_bundle).expanduser()
            return ssl.create_default_context(cafile=str(ca_bundle_path))

        return ssl.create_default_context(cafile=certifi.where())

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote

import httpx

from app import repositories
from app.config import settings
from app.schemas import ModelConnectionUpsert

Protocol = Literal["gemini", "openai_compatible"]

DEFAULT_BASE_URLS: dict[Protocol, str] = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta",
    "openai_compatible": "https://api.openai.com/v1",
}


@dataclass(frozen=True)
class ActiveModelRuntime:
    slot: int
    label: str
    protocol: Protocol
    base_url: str
    api_key: str
    model: str

    @property
    def provider_name(self) -> str:
        return f"{self.label}:{self.model}"


class SecretStore:
    """Small local-only API-key store.

    The file is under data/ and excluded from Git. Keys are never returned by the API.
    This is intentionally simple for a single-user desktop app; it is not a multi-user vault.
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path or settings.model_secrets_file

    def _read(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return {str(key): str(value) for key, value in payload.items() if value}

    def get(self, slot: int) -> str:
        return self._read().get(str(slot), "")

    def set(self, slot: int, api_key: str) -> None:
        payload = self._read()
        if api_key:
            payload[str(slot)] = api_key
        else:
            payload.pop(str(slot), None)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    def delete(self, slot: int) -> None:
        self.set(slot, "")


class ModelConnectionService:
    def __init__(self, *, secrets: SecretStore | None = None, client: httpx.Client | None = None) -> None:
        self.secrets = secrets or SecretStore()
        self.client = client

    @staticmethod
    def normalize_base_url(protocol: Protocol, base_url: str) -> str:
        value = (base_url or DEFAULT_BASE_URLS[protocol]).strip().rstrip("/")
        if not value.startswith(("http://", "https://")):
            raise ValueError("Base URL must start with http:// or https://")
        return value

    def list_public(self) -> list[dict[str, Any]]:
        stored = {int(item["slot"]): item for item in repositories.list_model_connections()}
        output: list[dict[str, Any]] = []
        for slot in (1, 2):
            item = stored.get(slot)
            if item is None:
                output.append(
                    {
                        "slot": slot,
                        "label": f"اتصال {slot}",
                        "protocol": "gemini" if slot == 1 else "openai_compatible",
                        "base_url": DEFAULT_BASE_URLS["gemini" if slot == 1 else "openai_compatible"],
                        "selected_model": "",
                        "active": False,
                        "has_api_key": False,
                        "cached_models": [],
                        "cache_updated_at": None,
                    }
                )
                continue
            public = dict(item)
            public["active"] = bool(public["active"])
            public["has_api_key"] = bool(self.secrets.get(slot))
            public["cached_models"] = self._decode_models(public.pop("cached_models_json", "[]"))
            output.append(public)
        return output

    def save(self, slot: int, payload: ModelConnectionUpsert) -> dict[str, Any]:
        self._validate_slot(slot)
        base_url = self.normalize_base_url(payload.protocol, payload.base_url)
        existing = repositories.get_model_connection(slot)
        repositories.upsert_model_connection(
            slot=slot,
            label=payload.label.strip() or f"اتصال {slot}",
            protocol=payload.protocol,
            base_url=base_url,
            selected_model=payload.selected_model.strip(),
            active=payload.active,
        )
        if payload.api_key is not None and payload.api_key.strip():
            self.secrets.set(slot, payload.api_key.strip())
        elif existing and str(existing.get("protocol")) != payload.protocol:
            # Never reuse a Gemini key silently after switching the slot to another protocol.
            self.secrets.delete(slot)
        return self.get_public(slot)

    def delete(self, slot: int) -> None:
        self._validate_slot(slot)
        repositories.delete_model_connection(slot)
        self.secrets.delete(slot)

    def get_public(self, slot: int) -> dict[str, Any]:
        self._validate_slot(slot)
        return next(item for item in self.list_public() if int(item["slot"]) == slot)

    def discover_models(self, slot: int) -> list[dict[str, Any]]:
        connection, api_key = self._require_connection(slot, require_model=False)
        models = self._discover(connection, api_key)
        repositories.cache_model_catalog(slot, models)
        return models

    def test_connection(self, slot: int) -> dict[str, Any]:
        runtime = self.get_runtime(slot)
        text = self.generate(runtime, "You are a connection test.", "Reply with exactly: OK", structured=False)
        return {"ok": bool(text.strip()), "response": text.strip()[:200], "provider": runtime.provider_name}

    def get_active_runtime(self) -> ActiveModelRuntime | None:
        connection = repositories.get_active_model_connection()
        if not connection:
            return None
        try:
            return self._runtime_from_connection(connection)
        except ValueError:
            return None

    def get_runtime(self, slot: int) -> ActiveModelRuntime:
        connection, _ = self._require_connection(slot, require_model=True)
        return self._runtime_from_connection(connection)

    def generate(
        self,
        runtime: ActiveModelRuntime,
        instructions: str,
        input_text: str,
        *,
        structured: bool,
    ) -> str:
        if runtime.protocol == "gemini":
            return self._generate_gemini(runtime, instructions, input_text, structured=structured)
        return self._generate_openai_compatible(runtime, instructions, input_text)

    def _runtime_from_connection(self, connection: dict[str, Any]) -> ActiveModelRuntime:
        slot = int(connection["slot"])
        api_key = self.secrets.get(slot)
        model = str(connection.get("selected_model") or "").strip()
        if not api_key:
            raise ValueError("API key is missing")
        if not model:
            raise ValueError("No model is selected")
        protocol = str(connection["protocol"])
        if protocol not in DEFAULT_BASE_URLS:
            raise ValueError("Unsupported protocol")
        return ActiveModelRuntime(
            slot=slot,
            label=str(connection["label"]),
            protocol=protocol,  # type: ignore[arg-type]
            base_url=self.normalize_base_url(protocol, str(connection["base_url"])),  # type: ignore[arg-type]
            api_key=api_key,
            model=model,
        )

    def _require_connection(self, slot: int, *, require_model: bool) -> tuple[dict[str, Any], str]:
        self._validate_slot(slot)
        connection = repositories.get_model_connection(slot)
        if not connection:
            raise ValueError("ابتدا تنظیمات اتصال را ذخیره کن.")
        api_key = self.secrets.get(slot)
        if not api_key:
            raise ValueError("کلید API برای این اتصال ثبت نشده است.")
        if require_model and not str(connection.get("selected_model") or "").strip():
            raise ValueError("ابتدا یک مدل را انتخاب کن.")
        return connection, api_key

    def _discover(self, connection: dict[str, Any], api_key: str) -> list[dict[str, Any]]:
        protocol = str(connection["protocol"])
        base_url = self.normalize_base_url(protocol, str(connection["base_url"]))  # type: ignore[arg-type]
        with self._client() as client:
            if protocol == "gemini":
                response = client.get(
                    f"{base_url}/models",
                    params={"pageSize": 1000},
                    headers={"x-goog-api-key": api_key},
                )
                self._raise_provider_error(response)
                data = response.json().get("models", [])
                models = []
                for item in data:
                    methods = item.get("supportedGenerationMethods") or item.get("supportedActions") or []
                    if "generateContent" not in methods:
                        continue
                    model_id = str(item.get("baseModelId") or item.get("name", "")).removeprefix("models/")
                    if not model_id:
                        continue
                    models.append(
                        {
                            "id": model_id,
                            "name": item.get("displayName") or model_id,
                            "description": item.get("description") or "",
                            "context_length": item.get("inputTokenLimit"),
                            "output_limit": item.get("outputTokenLimit"),
                            "thinking": bool(item.get("thinking", False)),
                            "free": None,
                        }
                    )
                return self._sort_models(models)

            response = client.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            self._raise_provider_error(response)
            data = response.json().get("data", [])
            models = []
            for item in data:
                model_id = str(item.get("id") or "").strip()
                if not model_id:
                    continue
                pricing = item.get("pricing") or {}
                prompt_price = self._number_or_none(pricing.get("prompt"))
                completion_price = self._number_or_none(pricing.get("completion"))
                free = (
                    prompt_price == 0 and completion_price == 0
                    if prompt_price is not None and completion_price is not None
                    else None
                )
                models.append(
                    {
                        "id": model_id,
                        "name": item.get("name") or model_id,
                        "description": item.get("description") or "",
                        "context_length": item.get("context_length"),
                        "output_limit": (item.get("top_provider") or {}).get("max_completion_tokens"),
                        "thinking": None,
                        "free": free,
                    }
                )
            return self._sort_models(models)

    def _generate_gemini(
        self,
        runtime: ActiveModelRuntime,
        instructions: str,
        input_text: str,
        *,
        structured: bool,
    ) -> str:
        payload: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": instructions}]},
            "contents": [{"role": "user", "parts": [{"text": input_text}]}],
            "generationConfig": {"temperature": 0.15},
        }
        if structured:
            payload["generationConfig"]["responseMimeType"] = "application/json"
        model_path = quote(runtime.model, safe="-._")
        with self._client() as client:
            response = client.post(
                f"{runtime.base_url}/models/{model_path}:generateContent",
                headers={"x-goog-api-key": runtime.api_key, "Content-Type": "application/json"},
                json=payload,
            )
            self._raise_provider_error(response)
            body = response.json()
        candidates = body.get("candidates") or []
        if not candidates:
            feedback = body.get("promptFeedback") or body
            raise RuntimeError(f"Gemini returned no candidate: {feedback}")
        parts = ((candidates[0].get("content") or {}).get("parts") or [])
        text = "".join(str(part.get("text") or "") for part in parts).strip()
        if not text:
            raise RuntimeError("Gemini returned an empty response.")
        return text

    def _generate_openai_compatible(
        self,
        runtime: ActiveModelRuntime,
        instructions: str,
        input_text: str,
    ) -> str:
        headers = {"Authorization": f"Bearer {runtime.api_key}", "Content-Type": "application/json"}
        chat_payload = {
            "model": runtime.model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": input_text},
            ],
            "temperature": 0.15,
        }
        with self._client() as client:
            chat_response = client.post(
                f"{runtime.base_url}/chat/completions",
                headers=headers,
                json=chat_payload,
            )
            if chat_response.is_success:
                return self._parse_chat_completion(chat_response.json())
            if chat_response.status_code not in {400, 404, 405, 422}:
                self._raise_provider_error(chat_response)

            # Some modern OpenAI-compatible services expose only the Responses API.
            responses_response = client.post(
                f"{runtime.base_url}/responses",
                headers=headers,
                json={"model": runtime.model, "instructions": instructions, "input": input_text},
            )
            if not responses_response.is_success:
                first_error = self._provider_error_text(chat_response)
                second_error = self._provider_error_text(responses_response)
                raise RuntimeError(
                    f"Chat Completions failed ({first_error}); Responses API failed ({second_error})"
                )
            return self._parse_responses_output(responses_response.json())

    @staticmethod
    def _parse_chat_completion(body: dict[str, Any]) -> str:
        choices = body.get("choices") or []
        if not choices:
            raise RuntimeError(f"Provider returned no choices: {body}")
        content = (choices[0].get("message") or {}).get("content")
        if isinstance(content, list):
            text = "".join(str(item.get("text") or "") for item in content if isinstance(item, dict))
        else:
            text = str(content or "")
        text = text.strip()
        if not text:
            raise RuntimeError("Provider returned an empty response.")
        return text

    @staticmethod
    def _parse_responses_output(body: dict[str, Any]) -> str:
        direct = str(body.get("output_text") or "").strip()
        if direct:
            return direct
        text_parts: list[str] = []
        for item in body.get("output") or []:
            for content in item.get("content") or []:
                if content.get("type") in {"output_text", "text"}:
                    text_parts.append(str(content.get("text") or ""))
        text = "".join(text_parts).strip()
        if not text:
            raise RuntimeError(f"Responses API returned no text: {body}")
        return text

    def _client(self):
        if self.client is not None:
            return _BorrowedClient(self.client)
        return httpx.Client(timeout=httpx.Timeout(90.0, connect=15.0), follow_redirects=True)

    @classmethod
    def _raise_provider_error(cls, response: httpx.Response) -> None:
        if response.is_success:
            return
        raise RuntimeError(cls._provider_error_text(response))

    @staticmethod
    def _provider_error_text(response: httpx.Response) -> str:
        detail: Any
        try:
            payload = response.json()
            detail = payload.get("error", payload)
        except ValueError:
            detail = response.text[:1000]
        return f"Provider HTTP {response.status_code}: {detail}"

    @staticmethod
    def _sort_models(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(models, key=lambda item: (not bool(item.get("free")), str(item.get("name") or item["id"]).lower()))

    @staticmethod
    def _decode_models(value: str) -> list[dict[str, Any]]:
        try:
            payload = json.loads(value or "[]")
        except json.JSONDecodeError:
            return []
        return payload if isinstance(payload, list) else []

    @staticmethod
    def _number_or_none(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _validate_slot(slot: int) -> None:
        if slot not in {1, 2}:
            raise ValueError("Only connection slots 1 and 2 are supported.")


class _BorrowedClient:
    """Make an injected httpx-like client usable in a with statement without closing it."""

    def __init__(self, client: Any) -> None:
        self.client = client

    def __enter__(self) -> Any:
        return self.client

    def __exit__(self, *_: Any) -> None:
        return None


model_connections = ModelConnectionService()

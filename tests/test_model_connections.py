from __future__ import annotations

import json

import httpx

from app.services.model_connection_service import model_connections


def _gemini_transport(grading_payload: dict | None = None) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path.endswith("/models"):
            assert request.headers["x-goog-api-key"] == "gemini-secret"
            return httpx.Response(
                200,
                json={
                    "models": [
                        {
                            "name": "models/gemini-dynamic-test",
                            "baseModelId": "gemini-dynamic-test",
                            "displayName": "Gemini Dynamic Test",
                            "description": "Returned by the provider, not hardcoded.",
                            "inputTokenLimit": 1000000,
                            "outputTokenLimit": 8192,
                            "supportedGenerationMethods": ["generateContent"],
                        },
                        {
                            "name": "models/text-embedding-test",
                            "baseModelId": "text-embedding-test",
                            "displayName": "Embedding only",
                            "supportedGenerationMethods": ["embedContent"],
                        },
                    ]
                },
            )
        if request.method == "POST" and ":generateContent" in request.url.path:
            payload = json.loads(request.content)
            assert payload["contents"][0]["role"] == "user"
            text = "OK" if grading_payload is None else json.dumps(grading_payload)
            return httpx.Response(
                200,
                json={"candidates": [{"content": {"parts": [{"text": text}]}}]},
            )
        return httpx.Response(404, json={"error": "unexpected request"})

    return httpx.MockTransport(handler)


def _grading_payload() -> dict:
    return {
        "max_score": 20,
        "total_score": 3,
        "score_breakdown": [
            {
                "criterion": "انتخاب روش",
                "max_score": 8,
                "awarded_score": 0,
                "rationale": "معادله خطی است و جداشدنی نیست.",
            },
            {
                "criterion": "مراحل حل",
                "max_score": 8,
                "awarded_score": 1,
                "rationale": "عامل انتگرال‌ساز و حل کامل نوشته نشده است.",
            },
            {
                "criterion": "تشخیص و توضیح",
                "max_score": 4,
                "awarded_score": 2,
                "rationale": "تلاش برای انتخاب روش دیده می‌شود اما نادرست است.",
            },
        ],
        "first_divergence": "فرض جداشدنی‌بودن معادله",
        "missing_steps": [
            {
                "step": "نوشتن معادله در فرم خطی",
                "impact": "روش حل از ابتدا اشتباه انتخاب شده است.",
                "suggested_fix": "معادله را به صورت y'-y=x نوشته و عامل انتگرال‌ساز را محاسبه کن.",
                "severity": "high",
            }
        ],
        "scientific_errors": ["این معادله جداشدنی نیست."],
        "calculation_errors": [],
        "notation_errors": [],
        "strengths": ["پاسخ کوتاه و روشن نوشته شده است."],
        "corrected_answer": "معادله خطی است و باید با عامل انتگرال‌ساز حل شود.",
        "likely_professor_score": {"minimum": 2, "maximum": 4, "scale_max": 20},
        "suggested_mistake": {
            "topic": "معادلات خطی مرتبه اول",
            "category": "تشخیص روش",
            "description": "معادله خطی به اشتباه جداشدنی تشخیص داده شد.",
            "prevention": "پیش از حل، ساختار معادله را طبقه‌بندی کن.",
            "severity": "high",
        },
        "confidence": 0.88,
    }


def test_model_connection_api_discovers_models_without_exposing_key(client, monkeypatch):
    fake_client = httpx.Client(transport=_gemini_transport())
    monkeypatch.setattr(model_connections, "client", fake_client)

    saved = client.put(
        "/api/model-connections/1",
        json={
            "label": "اتصال رایگان",
            "protocol": "gemini",
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "api_key": "gemini-secret",
            "selected_model": "",
            "active": True,
        },
    )
    assert saved.status_code == 200
    assert saved.json()["connection"]["has_api_key"] is True
    assert "api_key" not in saved.json()["connection"]

    discovered = client.post("/api/model-connections/1/discover")
    assert discovered.status_code == 200
    assert discovered.json()["count"] == 1
    assert discovered.json()["items"][0]["id"] == "gemini-dynamic-test"

    selected = client.put(
        "/api/model-connections/1",
        json={
            "label": "اتصال رایگان",
            "protocol": "gemini",
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "api_key": None,
            "selected_model": "gemini-dynamic-test",
            "active": True,
        },
    )
    assert selected.status_code == 200
    assert selected.json()["active_provider"] == "اتصال رایگان:gemini-dynamic-test"

    tested = client.post("/api/model-connections/1/test")
    assert tested.status_code == 200
    assert tested.json()["ok"] is True

    listing = client.get("/api/model-connections").json()
    assert listing["items"][0]["selected_model"] == "gemini-dynamic-test"
    assert listing["items"][0]["cached_models"][0]["id"] == "gemini-dynamic-test"
    assert "gemini-secret" not in json.dumps(listing)
    fake_client.close()


def test_real_model_runtime_replaces_demo_grader(client, monkeypatch):
    fake_client = httpx.Client(transport=_gemini_transport(_grading_payload()))
    monkeypatch.setattr(model_connections, "client", fake_client)

    client.put(
        "/api/model-connections/1",
        json={
            "label": "Gemini Test",
            "protocol": "gemini",
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "api_key": "gemini-secret",
            "selected_model": "gemini-dynamic-test",
            "active": True,
        },
    )
    course = client.post(
        "/api/courses",
        json={
            "name": "معادلات دیفرانسیل",
            "professor": "استاد تست",
            "term": "1405-1",
            "exam_date": "",
            "target_grade": 20,
            "daily_minutes": 90,
            "exam_scope": "فصل اول",
            "notes": "",
        },
    ).json()["course"]

    response = client.post(
        f"/api/courses/{course['id']}/run",
        json={
            "mode": "grade",
            "prompt": "صورت سؤال: y'=x+y را حل کنید. پاسخ من: معادله را جدا کرده و انتگرال می‌گیریم. بارم: 20",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "Gemini Test:gemini-dynamic-test"
    assert payload["validation_status"] == "valid"
    assert payload["structured_output"]["total_score"] == 3
    fake_client.close()


def test_only_two_connection_slots_are_allowed(client):
    response = client.put(
        "/api/model-connections/3",
        json={
            "label": "Invalid",
            "protocol": "openai_compatible",
            "base_url": "https://example.com/v1",
            "api_key": "secret",
            "selected_model": "model",
            "active": False,
        },
    )
    assert response.status_code == 400


def test_openai_compatible_model_discovery_is_dynamic(client, monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path.endswith("/models"):
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": "vendor/model-from-api",
                            "name": "Model From API",
                            "description": "Dynamic catalog entry",
                            "context_length": 128000,
                            "pricing": {"prompt": "0", "completion": "0"},
                        }
                    ]
                },
            )
        return httpx.Response(404)

    fake_client = httpx.Client(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(model_connections, "client", fake_client)
    client.put(
        "/api/model-connections/2",
        json={
            "label": "سرویس دوم",
            "protocol": "openai_compatible",
            "base_url": "https://router.example/v1/",
            "api_key": "router-key",
            "selected_model": "",
            "active": False,
        },
    )
    result = client.post("/api/model-connections/2/discover")
    assert result.status_code == 200
    assert result.json()["items"] == [
        {
            "id": "vendor/model-from-api",
            "name": "Model From API",
            "description": "Dynamic catalog entry",
            "context_length": 128000,
            "output_limit": None,
            "thinking": None,
            "free": True,
        }
    ]
    fake_client.close()


def test_switching_protocol_without_new_key_does_not_reuse_old_secret(client):
    client.put(
        "/api/model-connections/1",
        json={
            "label": "Gemini",
            "protocol": "gemini",
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "api_key": "gemini-secret",
            "selected_model": "gemini-test",
            "active": True,
        },
    )
    switched = client.put(
        "/api/model-connections/1",
        json={
            "label": "Other API",
            "protocol": "openai_compatible",
            "base_url": "https://example.com/v1",
            "api_key": None,
            "selected_model": "other-model",
            "active": True,
        },
    )
    assert switched.status_code == 200
    assert switched.json()["connection"]["has_api_key"] is False
    assert switched.json()["active_provider"] is None


def test_openai_compatible_generation_falls_back_to_responses_api(client, monkeypatch):
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/chat/completions"):
            return httpx.Response(404, json={"error": {"message": "Use Responses API"}})
        if request.url.path.endswith("/responses"):
            return httpx.Response(200, json={"output_text": "OK"})
        return httpx.Response(404)

    fake_client = httpx.Client(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(model_connections, "client", fake_client)
    client.put(
        "/api/model-connections/2",
        json={
            "label": "Responses provider",
            "protocol": "openai_compatible",
            "base_url": "https://provider.example/v1",
            "api_key": "secret",
            "selected_model": "reasoning-model",
            "active": True,
        },
    )
    tested = client.post("/api/model-connections/2/test")
    assert tested.status_code == 200
    assert calls == ["/v1/chat/completions", "/v1/responses"]
    fake_client.close()

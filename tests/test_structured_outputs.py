from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.config import settings
from app.schemas import GradingReport, ProfessorProfile, StudyPlan, structured_model_for_mode
from app.services.llm_service import (
    EvidenceValidationError,
    LLMService,
    extract_json_object,
    validate_structured_response,
)
from app.services.prompt_service import build_prompt


def profile_payload(*, source_number: int = 1, filename: str = "notes.txt", chunk_index: int = 0) -> dict:
    return {
        "course_name": "Probability 2",
        "professor_name": "Professor A",
        "evidence_count": 1,
        "claims": [
            {
                "category": "grading_pattern",
                "claim": "Writing assumptions explicitly appears important.",
                "evidence_refs": [
                    {
                        "source_number": source_number,
                        "filename": filename,
                        "chunk_index": chunk_index,
                        "support": "The class example writes the independence assumption before calculation.",
                    }
                ],
                "confidence": 0.75,
                "status": "inferred",
            }
        ],
        "unknowns": [],
        "recommended_exam_strategy": ["State assumptions before applying a distribution."],
        "limitations": ["Only one evidence chunk is available."],
        "overall_confidence": 0.55,
    }


def evidence_pack() -> list[dict]:
    return [{"filename": "notes.txt", "chunk_index": 0, "content": "Assumptions are stated explicitly."}]


class FakeResponses:
    def __init__(self, outputs: list[str | Exception]):
        self.outputs = iter(outputs)
        self.call_count = 0

    def create(self, **_: object) -> SimpleNamespace:
        self.call_count += 1
        output = next(self.outputs)
        if isinstance(output, Exception):
            raise output
        return SimpleNamespace(output_text=output)


class FakeClient:
    def __init__(self, outputs: list[str | Exception]):
        self.responses = FakeResponses(outputs)


def test_structured_mode_mapping_is_explicit():
    assert structured_model_for_mode("profile") is ProfessorProfile
    assert structured_model_for_mode("grade") is GradingReport
    assert structured_model_for_mode("plan") is StudyPlan
    assert structured_model_for_mode("teach") is None


def test_profile_prompt_contains_json_contract():
    instructions, _ = build_prompt(
        {"name": "Probability 2", "professor": "Professor A", "daily_minutes": 90},
        "profile",
        "پروفایل را بساز",
        evidence_pack(),
    )
    assert "ProfessorProfile" in instructions
    assert "فقط و فقط یک JSON معتبر" in instructions
    assert '"evidence_refs"' in instructions
    assert "source_number، filename و chunk_index" in instructions


def test_unstructured_prompt_does_not_include_json_contract():
    instructions, _ = build_prompt(
        {"name": "Probability 2", "professor": "Professor A", "daily_minutes": 90},
        "teach",
        "قضیه بیز را آموزش بده",
        [],
    )
    assert "JSON Schema" not in instructions


def test_json_extraction_accepts_code_fence():
    assert extract_json_object('```json\n{"ok": true}\n```') == {"ok": True}


def test_profile_validation_requires_evidence_for_supported_claim():
    payload = profile_payload()
    payload["claims"][0]["status"] = "supported"
    payload["claims"][0]["evidence_refs"] = []
    with pytest.raises(ValidationError):
        ProfessorProfile.model_validate(payload)


def test_grading_report_rejects_inconsistent_totals():
    with pytest.raises(ValidationError):
        GradingReport.model_validate(
            {
                "max_score": 20,
                "total_score": 15,
                "score_breakdown": [
                    {
                        "criterion": "Method",
                        "max_score": 20,
                        "awarded_score": 14,
                        "rationale": "One point does not match the declared total.",
                    }
                ],
                "missing_steps": [],
                "scientific_errors": [],
                "calculation_errors": [],
                "notation_errors": [],
                "strengths": [],
                "corrected_answer": "",
                "confidence": 0.8,
            }
        )


def test_structured_parser_validates_profile_and_real_evidence():
    model = validate_structured_response(
        json.dumps(profile_payload()),
        ProfessorProfile,
        evidence_pack(),
    )
    assert isinstance(model, ProfessorProfile)
    assert model.claims[0].confidence == 0.75


def test_hallucinated_source_number_is_rejected():
    with pytest.raises(EvidenceValidationError, match="source_number=7 does not exist"):
        validate_structured_response(
            json.dumps(profile_payload(source_number=7)),
            ProfessorProfile,
            evidence_pack(),
        )


def test_mismatched_filename_is_rejected():
    with pytest.raises(EvidenceValidationError, match="filename mismatch"):
        validate_structured_response(
            json.dumps(profile_payload(filename="invented.pdf")),
            ProfessorProfile,
            evidence_pack(),
        )


def test_mismatched_chunk_index_is_rejected():
    with pytest.raises(EvidenceValidationError, match="chunk_index mismatch"):
        validate_structured_response(
            json.dumps(profile_payload(chunk_index=9)),
            ProfessorProfile,
            evidence_pack(),
        )


def test_invalid_structured_response_falls_back_to_raw_text():
    result = LLMService._validated_result(
        "This is not JSON.",
        "test-provider",
        ProfessorProfile,
        evidence_pack(),
    )
    assert result.structured_output is None
    assert result.text == "This is not JSON."
    assert result.schema_name == "ProfessorProfile"
    assert result.validation_error
    assert result.validation_status == "invalid_fallback"


def test_invalid_first_response_is_repaired_once(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "openai_model", "test-model")
    invalid = json.dumps(profile_payload(source_number=7))
    repaired = json.dumps(profile_payload(source_number=1))

    service = LLMService()
    service.enabled = True
    service.client = FakeClient([invalid, repaired])

    result = service.generate(
        "Return ProfessorProfile JSON.",
        "Build the profile.",
        response_model=ProfessorProfile,
        evidence=evidence_pack(),
    )

    assert result.validation_status == "recovered"
    assert result.retry_count == 1
    assert result.structured_output is not None
    assert result.first_validation_error and "source_number=7" in result.first_validation_error
    assert service.client.responses.call_count == 2


def test_failed_repair_remains_explicit_invalid_fallback(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "openai_model", "test-model")
    service = LLMService()
    service.enabled = True
    service.client = FakeClient(["not json", "still not json"])

    result = service.generate(
        "Return ProfessorProfile JSON.",
        "Build the profile.",
        response_model=ProfessorProfile,
        evidence=evidence_pack(),
    )

    assert result.structured_output is None
    assert result.validation_status == "invalid_fallback"
    assert result.retry_count == 1
    assert "First attempt failed" in (result.validation_error or "")
    assert "Repair attempt failed" in (result.validation_error or "")
    assert service.client.responses.call_count == 2




def test_failed_repair_request_returns_first_raw_response(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "openai_model", "test-model")
    service = LLMService()
    service.enabled = True
    service.client = FakeClient(["not json", RuntimeError("temporary provider error")])

    result = service.generate(
        "Return ProfessorProfile JSON.",
        "Build the profile.",
        response_model=ProfessorProfile,
        evidence=evidence_pack(),
    )

    assert result.text == "not json"
    assert result.validation_status == "invalid_fallback"
    assert result.retry_count == 1
    assert "Repair request failed before validation" in (result.validation_error or "")

def test_demo_profile_endpoint_returns_valid_structured_output(client):
    response = client.post(
        "/courses",
        data={"name": "Mathematical Statistics", "professor": "Professor B", "daily_minutes": "90"},
        follow_redirects=False,
    )
    course_id = int(response.headers["location"].split("/")[-1])

    run = client.post(
        f"/api/courses/{course_id}/run",
        json={"mode": "profile", "prompt": "پروفایل اولیه را بساز"},
    )
    assert run.status_code == 200
    payload = run.json()
    assert payload["schema"] == "ProfessorProfile"
    assert payload["validation_error"] is None
    assert payload["validation_status"] == "valid"
    assert payload["retry_count"] == 0
    ProfessorProfile.model_validate(payload["structured_output"])


def test_invalid_fallback_is_persisted_with_explicit_warning():
    from app.services.exam_coach_service import persisted_run_output
    from app.services.llm_service import LLMResult

    result = LLMResult(
        text="raw invalid output",
        provider="test",
        schema_name="ProfessorProfile",
        validation_error="bad citation",
        validation_status="invalid_fallback",
        retry_count=1,
    )
    persisted = persisted_run_output(result)
    assert "STRUCTURED OUTPUT INVALID" in persisted
    assert "bad citation" in persisted
    assert persisted.endswith("raw invalid output")

from __future__ import annotations

from dataclasses import dataclass, replace
import json
import re
from typing import Any, Iterator, Literal

from pydantic import BaseModel, ValidationError

from app.config import settings
from app.schemas import (
    EvidenceReference,
    GradingReport,
    ProfessorProfile,
    StudyPlan,
    StructuredOutputModel,
)

ValidationStatus = Literal["not_applicable", "valid", "recovered", "invalid_fallback"]


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider: str
    structured_output: dict[str, Any] | None = None
    schema_name: str | None = None
    validation_error: str | None = None
    validation_status: ValidationStatus = "not_applicable"
    retry_count: int = 0
    first_validation_error: str | None = None


class EvidenceValidationError(ValueError):
    """Raised when a model cites evidence that was not supplied in the current run."""


def extract_json_object(raw_text: str) -> dict[str, Any]:
    """Extract one JSON object from plain text or a fenced model response."""

    candidate = raw_text.strip()
    fence_match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", candidate, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        candidate = fence_match.group(1).strip()

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("No JSON object was found in the model response.")
        payload = json.loads(candidate[start : end + 1])

    if not isinstance(payload, dict):
        raise ValueError("The structured model response must be a JSON object.")
    return payload


def _iter_evidence_references(value: Any) -> Iterator[EvidenceReference]:
    if isinstance(value, EvidenceReference):
        yield value
        return
    if isinstance(value, BaseModel):
        for field_name in value.__class__.model_fields:
            yield from _iter_evidence_references(getattr(value, field_name))
        return
    if isinstance(value, dict):
        for item in value.values():
            yield from _iter_evidence_references(item)
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _iter_evidence_references(item)


def validate_evidence_references(parsed: BaseModel, evidence: list[dict[str, Any]]) -> None:
    """Cross-check every structured citation against the exact retrieved evidence list."""

    catalog = {index: item for index, item in enumerate(evidence, start=1)}
    errors: list[str] = []

    for reference in _iter_evidence_references(parsed):
        actual = catalog.get(reference.source_number)
        if actual is None:
            errors.append(
                f"source_number={reference.source_number} does not exist; "
                f"allowed source numbers are 1..{len(evidence)}."
            )
            continue

        expected_filename = str(actual.get("filename", ""))
        if reference.filename != expected_filename:
            errors.append(
                f"source_number={reference.source_number} filename mismatch: "
                f"expected {expected_filename!r}, received {reference.filename!r}."
            )

        expected_chunk = actual.get("chunk_index")
        if reference.chunk_index != expected_chunk:
            errors.append(
                f"source_number={reference.source_number} chunk_index mismatch: "
                f"expected {expected_chunk!r}, received {reference.chunk_index!r}."
            )

    if errors:
        raise EvidenceValidationError("Invalid evidence reference(s): " + " ".join(errors))


def validate_structured_response(
    raw_text: str,
    response_model: StructuredOutputModel,
    evidence: list[dict[str, Any]],
) -> BaseModel:
    payload = extract_json_object(raw_text)
    parsed = response_model.model_validate(payload)
    validate_evidence_references(parsed, evidence)
    return parsed


class LLMService:
    def __init__(self) -> None:
        self.enabled = bool(settings.openai_api_key and settings.openai_model)
        self.client: Any | None = None
        if self.enabled:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError(
                    "OPENAI_API_KEY and OPENAI_MODEL are set, but the openai package is not installed."
                ) from exc
            self.client = OpenAI(api_key=settings.openai_api_key)

    def generate(
        self,
        instructions: str,
        input_text: str,
        response_model: StructuredOutputModel | None = None,
        evidence: list[dict[str, Any]] | None = None,
    ) -> LLMResult:
        evidence = evidence or []
        if not self.enabled or self.client is None:
            return self._demo_result(input_text, response_model)

        raw_text = self._request_model(instructions, input_text)
        provider = f"openai:{settings.openai_model}"
        if response_model is None:
            return LLMResult(text=raw_text, provider=provider)

        first_result = self._validated_result(raw_text, provider, response_model, evidence)
        if first_result.structured_output is not None:
            return first_result

        repair_input = self._repair_input(
            original_input=input_text,
            invalid_output=raw_text,
            validation_error=first_result.validation_error or "Unknown validation error.",
            evidence=evidence,
        )
        try:
            repaired_raw_text = self._request_model(instructions, repair_input)
        except Exception as exc:
            return replace(
                first_result,
                validation_error=(
                    f"First attempt failed: {first_result.validation_error}\n"
                    f"Repair request failed before validation: {exc}"
                ),
                validation_status="invalid_fallback",
                retry_count=1,
                first_validation_error=first_result.validation_error,
            )

        repaired_result = self._validated_result(repaired_raw_text, provider, response_model, evidence)

        if repaired_result.structured_output is not None:
            return replace(
                repaired_result,
                validation_status="recovered",
                retry_count=1,
                first_validation_error=first_result.validation_error,
            )

        combined_error = (
            "First attempt failed: "
            f"{first_result.validation_error}\n"
            "Repair attempt failed: "
            f"{repaired_result.validation_error}"
        )
        return replace(
            repaired_result,
            validation_error=combined_error,
            validation_status="invalid_fallback",
            retry_count=1,
            first_validation_error=first_result.validation_error,
        )

    def _request_model(self, instructions: str, input_text: str) -> str:
        if self.client is None:
            raise RuntimeError("Language model client is not initialized.")
        response = self.client.responses.create(
            model=settings.openai_model,
            instructions=instructions,
            input=input_text,
        )
        raw_text = response.output_text.strip()
        if not raw_text:
            raise RuntimeError("The language model returned an empty response.")
        return raw_text

    @staticmethod
    def _repair_input(
        original_input: str,
        invalid_output: str,
        validation_error: str,
        evidence: list[dict[str, Any]],
    ) -> str:
        allowed_evidence = [
            {
                "source_number": index,
                "filename": item.get("filename"),
                "chunk_index": item.get("chunk_index"),
            }
            for index, item in enumerate(evidence, start=1)
        ]
        return (
            f"{original_input}\n\n"
            "اصلاح اجباری خروجی قبلی:\n"
            "خروجی قبلی قرارداد ساختاریافته را نقض کرده است. فقط یک JSON اصلاح‌شده و بدون Markdown برگردان. "
            "هیچ ادعا یا ارجاع جدیدی اختراع نکن.\n\n"
            f"خطای اعتبارسنجی:\n{validation_error}\n\n"
            "فهرست دقیق ارجاعات مجاز:\n"
            f"{json.dumps(allowed_evidence, ensure_ascii=False, indent=2)}\n\n"
            "خروجی نامعتبر قبلی:\n"
            f"{invalid_output[:30000]}"
        )

    @staticmethod
    def _validated_result(
        raw_text: str,
        provider: str,
        response_model: StructuredOutputModel,
        evidence: list[dict[str, Any]],
    ) -> LLMResult:
        try:
            parsed = validate_structured_response(raw_text, response_model, evidence)
        except (ValueError, json.JSONDecodeError, ValidationError, EvidenceValidationError) as exc:
            return LLMResult(
                text=raw_text,
                provider=provider,
                schema_name=response_model.__name__,
                validation_error=str(exc),
                validation_status="invalid_fallback",
            )

        structured_output = parsed.model_dump(mode="json")
        return LLMResult(
            text=json.dumps(structured_output, ensure_ascii=False, indent=2),
            provider=provider,
            structured_output=structured_output,
            schema_name=response_model.__name__,
            validation_status="valid",
        )

    def _demo_result(
        self,
        input_text: str,
        response_model: StructuredOutputModel | None,
    ) -> LLMResult:
        if response_model is None:
            return LLMResult(text=self._demo_response(input_text), provider="demo")

        demo_model = self._demo_structured_model(response_model)
        structured_output = demo_model.model_dump(mode="json")
        return LLMResult(
            text=json.dumps(structured_output, ensure_ascii=False, indent=2),
            provider="demo",
            structured_output=structured_output,
            schema_name=response_model.__name__,
            validation_status="valid",
        )

    @staticmethod
    def _demo_structured_model(response_model: StructuredOutputModel) -> BaseModel:
        if response_model is ProfessorProfile:
            return ProfessorProfile(
                course_name="درس آزمایشی",
                professor_name="نامشخص",
                evidence_count=0,
                claims=[
                    {
                        "category": "unknown",
                        "claim": "برای استنباط سبک استاد هنوز شواهد کافی وجود ندارد.",
                        "evidence_refs": [],
                        "confidence": 0.1,
                        "status": "unknown",
                    }
                ],
                unknowns=["نمونه پاسخ نمره‌گذاری‌شده موجود نیست."],
                recommended_exam_strategy=["منابع رسمی درس و پاسخ‌های تصحیح‌شده را اضافه کن."],
                limitations=["این خروجی در حالت آزمایشی ساخته شده است."],
                overall_confidence=0.1,
            )

        if response_model is GradingReport:
            return GradingReport(
                max_score=20,
                total_score=0,
                score_breakdown=[
                    {
                        "criterion": "ارزیابی واقعی پاسخ",
                        "max_score": 20,
                        "awarded_score": 0,
                        "rationale": "در حالت آزمایشی مدل زبانی متصل نیست و پاسخ علمی تصحیح نشده است.",
                    }
                ],
                first_divergence=None,
                missing_steps=[],
                scientific_errors=[],
                calculation_errors=[],
                notation_errors=[],
                strengths=[],
                corrected_answer="",
                likely_professor_score=None,
                suggested_mistake=None,
                confidence=0,
            )

        if response_model is StudyPlan:
            return StudyPlan(
                course_name="درس آزمایشی",
                target_grade=None,
                daily_minutes=90,
                duration_days=1,
                assumptions=["مدل زبانی متصل نیست و برنامه صرفاً برای تست قرارداد داده است."],
                priorities=[],
                days=[
                    {
                        "day_number": 1,
                        "calendar_date": None,
                        "focus": "تکمیل منابع و فعال‌کردن مدل",
                        "tasks": [
                            {
                                "title": "منابع رسمی درس را بارگذاری کن.",
                                "task_type": "review",
                                "estimated_minutes": 90,
                                "exercise_count": None,
                                "completion_criteria": "حداقل یک منبع قابل بازیابی در workspace وجود داشته باشد.",
                            }
                        ],
                        "short_test": None,
                        "total_minutes": 90,
                    }
                ],
                final_review=[],
                risk_controls=["این برنامه را به‌عنوان برنامه مطالعاتی واقعی استفاده نکن."],
                confidence=0,
            )

        raise ValueError(f"No demo payload is defined for {response_model.__name__}.")

    @staticmethod
    def _demo_response(input_text: str) -> str:
        request = input_text.split("درخواست دانشجو:")[-1].strip()
        return (
            "## حالت آزمایشی\n\n"
            "اتصال مدل هنوز فعال نیست، اما بازیابی منابع و ذخیره‌سازی درخواست درست انجام شد.\n\n"
            f"**درخواست ثبت‌شده:** {request[:1000]}\n\n"
            "برای فعال‌شدن پاسخ هوشمند، `OPENAI_API_KEY` و `OPENAI_MODEL` را در فایل `.env` وارد کن. "
            "تا آن زمان می‌توانی دوره، منابع، قطعه‌بندی، تاریخچه اجراها و دفترچه خطا را آزمایش کنی."
        )

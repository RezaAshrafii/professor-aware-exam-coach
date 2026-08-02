from __future__ import annotations

from typing import Any

from app import repositories
from app.config import settings
from app.schemas import structured_model_for_mode
from app.services.llm_service import LLMResult, LLMService
from app.services.prompt_service import build_prompt
from app.services.retrieval_service import retrieve


def persisted_run_output(result: LLMResult) -> str:
    if result.validation_status != "invalid_fallback":
        return result.text
    return (
        "⚠ STRUCTURED OUTPUT INVALID — DO NOT TREAT AS A VALID REPORT\n"
        "The schema/evidence validation failed after the repair attempt.\n"
        f"Validation error: {result.validation_error or 'unknown'}\n\n"
        "Raw model output:\n"
        f"{result.text}"
    )


class ExamCoachService:
    def __init__(self) -> None:
        self.llm = LLMService()

    def run(self, course: dict[str, Any], mode: str, user_input: str) -> dict[str, Any]:
        chunks = repositories.list_chunks(int(course["id"]))
        query = f"{mode} {course.get('exam_scope', '')} {user_input}"
        evidence = retrieve(query, chunks, limit=settings.max_context_chunks)
        instructions, input_text = build_prompt(course, mode, user_input, evidence)
        response_model = structured_model_for_mode(mode)
        result = self.llm.generate(
            instructions,
            input_text,
            response_model=response_model,
            evidence=evidence,
        )
        evidence_summary = [
            {
                "source_id": item["source_id"],
                "filename": item["filename"],
                "chunk_index": item["chunk_index"],
                "score": item.get("score", 0),
            }
            for item in evidence
        ]
        run_id = repositories.save_run(
            int(course["id"]),
            mode,
            user_input,
            persisted_run_output(result),
            evidence_summary,
            result.provider,
        )
        return {
            "id": run_id,
            "output": result.text,
            "provider": result.provider,
            "evidence": evidence,
            "structured_output": result.structured_output,
            "schema": result.schema_name,
            "validation_error": result.validation_error,
            "validation_status": result.validation_status,
            "retry_count": result.retry_count,
            "first_validation_error": result.first_validation_error,
        }

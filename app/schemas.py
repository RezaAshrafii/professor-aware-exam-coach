from __future__ import annotations

from datetime import date
from typing import Literal, TypeAlias

from pydantic import BaseModel, Field, field_validator, model_validator


def _contains_persian(value: str) -> bool:
    return any("\u0600" <= character <= "\u06FF" for character in value)



class CourseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    professor: str = Field(default="", max_length=120)
    term: str = Field(default="", max_length=60)
    exam_date: str = Field(default="", max_length=30)
    target_grade: float | None = Field(default=None, ge=0, le=20)
    daily_minutes: int = Field(default=90, ge=10, le=720)
    exam_scope: str = Field(default="", max_length=5000)
    notes: str = Field(default="", max_length=5000)


class RunRequest(BaseModel):
    mode: str
    prompt: str = Field(min_length=1, max_length=20000)


class MistakeCreate(BaseModel):
    topic: str = Field(default="", max_length=200)
    category: str = Field(default="", max_length=100)
    description: str = Field(min_length=1, max_length=3000)
    prevention: str = Field(default="", max_length=3000)
    severity: str = Field(default="medium", pattern="^(low|medium|high)$")


class ExampleCardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    topic: str = Field(default="", max_length=200)
    question: str = Field(min_length=1, max_length=10000)
    solution: str = Field(min_length=1, max_length=20000)
    method_name: str = Field(default="", max_length=200)
    source_kind: Literal[
        "class_note", "board_photo", "video_clip", "cleaned_transcript", "other"
    ] = "class_note"
    source_reference: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=3000)
    status: Literal["draft", "confirmed"] = "draft"


class ExampleCardStatusUpdate(BaseModel):
    status: Literal["draft", "confirmed"]


class ModelConnectionUpsert(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    protocol: Literal["gemini", "openai_compatible"]
    base_url: str = Field(default="", max_length=500)
    api_key: str | None = Field(default=None, max_length=2000)
    selected_model: str = Field(default="", max_length=300)
    active: bool = False


class ModelSelectionUpdate(BaseModel):
    selected_model: str = Field(min_length=1, max_length=300)
    active: bool = True


class EvidenceReference(BaseModel):
    """Reference to one retrieved chunk shown to the model in the current run."""

    source_number: int = Field(ge=1)
    filename: str = Field(min_length=1, max_length=500)
    chunk_index: int | None = Field(default=None, ge=0)
    support: str = Field(
        min_length=1,
        max_length=1200,
        description="Short paraphrase of how this chunk supports the claim; do not invent quotations.",
    )


class ProfessorClaim(BaseModel):
    category: Literal[
        "teaching_style",
        "notation",
        "preferred_method",
        "exam_pattern",
        "grading_pattern",
        "risk",
        "unknown",
    ]
    claim: str = Field(min_length=1, max_length=2000)
    evidence_refs: list[EvidenceReference] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    status: Literal["supported", "inferred", "unknown"]

    @model_validator(mode="after")
    def evidence_matches_status(self) -> ProfessorClaim:
        if self.status == "supported" and not self.evidence_refs:
            raise ValueError("A supported claim must include at least one evidence reference.")
        if self.status == "unknown" and self.confidence > 0.25:
            raise ValueError("Unknown claims must have confidence at or below 0.25.")
        return self


class ProfessorProfile(BaseModel):
    course_name: str = Field(min_length=1, max_length=200)
    professor_name: str = Field(min_length=1, max_length=200)
    evidence_count: int = Field(ge=0)
    claims: list[ProfessorClaim]
    unknowns: list[str] = Field(default_factory=list)
    recommended_exam_strategy: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0, le=1)


class ScoreBreakdownItem(BaseModel):
    criterion: str = Field(min_length=1, max_length=500)
    max_score: float = Field(gt=0)
    awarded_score: float = Field(ge=0)
    rationale: str = Field(min_length=1, max_length=2000)

    @field_validator("criterion", "rationale")
    @classmethod
    def narrative_must_be_persian(cls, value: str) -> str:
        if not _contains_persian(value):
            raise ValueError("Grading criteria and rationales must be written in Persian.")
        return value

    @model_validator(mode="after")
    def awarded_does_not_exceed_max(self) -> ScoreBreakdownItem:
        if self.awarded_score > self.max_score:
            raise ValueError("awarded_score cannot exceed max_score.")
        return self


class MissingStep(BaseModel):
    step: str = Field(min_length=1, max_length=1200)
    impact: str = Field(min_length=1, max_length=1200)
    suggested_fix: str = Field(min_length=1, max_length=2000)
    severity: Literal["low", "medium", "high"]

    @field_validator("step", "impact", "suggested_fix")
    @classmethod
    def explanation_must_be_persian(cls, value: str) -> str:
        if not _contains_persian(value):
            raise ValueError("Missing-step explanations must be written in Persian.")
        return value


class ScoreRange(BaseModel):
    minimum: float = Field(ge=0)
    maximum: float = Field(ge=0)
    scale_max: float = Field(gt=0)

    @model_validator(mode="after")
    def range_is_valid(self) -> ScoreRange:
        if self.minimum > self.maximum:
            raise ValueError("minimum cannot exceed maximum.")
        if self.maximum > self.scale_max:
            raise ValueError("maximum cannot exceed scale_max.")
        return self


class MistakeSuggestion(BaseModel):
    topic: str = Field(default="", max_length=200)
    category: str = Field(default="", max_length=100)
    description: str = Field(min_length=1, max_length=3000)
    prevention: str = Field(default="", max_length=3000)
    severity: Literal["low", "medium", "high"] = "medium"


class GradingReport(BaseModel):
    max_score: float = Field(gt=0)
    total_score: float = Field(ge=0)
    score_breakdown: list[ScoreBreakdownItem] = Field(min_length=1)
    first_divergence: str | None = Field(default=None, max_length=2000)
    missing_steps: list[MissingStep] = Field(default_factory=list)
    scientific_errors: list[str] = Field(default_factory=list)
    calculation_errors: list[str] = Field(default_factory=list)
    notation_errors: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    corrected_answer: str = Field(default="", max_length=20000)
    likely_professor_score: ScoreRange | None = None
    suggested_mistake: MistakeSuggestion | None = None
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def totals_are_consistent(self) -> GradingReport:
        if self.total_score > self.max_score:
            raise ValueError("total_score cannot exceed max_score.")
        breakdown_max = sum(item.max_score for item in self.score_breakdown)
        breakdown_awarded = sum(item.awarded_score for item in self.score_breakdown)
        tolerance = 0.02
        if abs(breakdown_max - self.max_score) > tolerance:
            raise ValueError("The score_breakdown max scores must sum to max_score.")
        if abs(breakdown_awarded - self.total_score) > tolerance:
            raise ValueError("The score_breakdown awarded scores must sum to total_score.")
        return self


class StudyPriority(BaseModel):
    topic: str = Field(min_length=1, max_length=300)
    priority: Literal["essential", "high", "medium", "low"]
    reason: str = Field(min_length=1, max_length=1200)
    evidence_refs: list[EvidenceReference] = Field(default_factory=list)


class StudyTask(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    task_type: Literal["learn", "review", "practice", "mock_exam", "error_review"]
    estimated_minutes: int = Field(ge=5, le=720)
    exercise_count: int | None = Field(default=None, ge=0, le=500)
    completion_criteria: str = Field(min_length=1, max_length=1500)


class StudyDay(BaseModel):
    day_number: int = Field(ge=1)
    calendar_date: date | None = None
    focus: str = Field(min_length=1, max_length=500)
    tasks: list[StudyTask] = Field(min_length=1)
    short_test: str | None = Field(default=None, max_length=1500)
    total_minutes: int = Field(ge=5, le=1440)

    @model_validator(mode="after")
    def task_minutes_match_total(self) -> StudyDay:
        task_total = sum(task.estimated_minutes for task in self.tasks)
        if task_total != self.total_minutes:
            raise ValueError("StudyDay total_minutes must equal the sum of task estimated_minutes.")
        return self


class StudyPlan(BaseModel):
    course_name: str = Field(min_length=1, max_length=200)
    target_grade: float | None = Field(default=None, ge=0, le=20)
    daily_minutes: int = Field(ge=10, le=720)
    duration_days: int = Field(ge=1, le=365)
    assumptions: list[str] = Field(default_factory=list)
    priorities: list[StudyPriority] = Field(default_factory=list)
    days: list[StudyDay] = Field(min_length=1)
    final_review: list[str] = Field(default_factory=list)
    risk_controls: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def day_count_is_consistent(self) -> StudyPlan:
        if len(self.days) != self.duration_days:
            raise ValueError("duration_days must equal the number of day entries.")
        expected = list(range(1, self.duration_days + 1))
        actual = [day.day_number for day in self.days]
        if actual != expected:
            raise ValueError("Study plan day numbers must be consecutive and start at 1.")
        return self


StructuredOutputModel: TypeAlias = type[ProfessorProfile] | type[GradingReport] | type[StudyPlan]

STRUCTURED_MODELS: dict[str, StructuredOutputModel] = {
    "profile": ProfessorProfile,
    "grade": GradingReport,
    "plan": StudyPlan,
}


def structured_model_for_mode(mode: str) -> StructuredOutputModel | None:
    return STRUCTURED_MODELS.get(mode)

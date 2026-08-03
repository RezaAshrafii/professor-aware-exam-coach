import type { CoachResponse, MistakeInput } from "@/lib/types";

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function text(value: unknown): string {
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  return "";
}

function numberValue(value: unknown): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function looksLikeMath(line: string): boolean {
  const trimmed = line.trim();
  if (!trimmed) return false;
  const mathSignals = (trimmed.match(/[=^_\\∫∑√μλ∞±×÷<>]/g) ?? []).length;
  const latinSignals = (trimmed.match(/[A-Za-z]/g) ?? []).length;
  const persianSignals = (trimmed.match(/[\u0600-\u06FF]/g) ?? []).length;
  return mathSignals > 0 && (latinSignals >= persianSignals || trimmed.length < 90);
}

function RichText({ value, compact = false }: { value: string; compact?: boolean }) {
  const lines = value.split(/\r?\n/);
  return (
    <div className={`rich-text ${compact ? "compact" : ""}`}>
      {lines.map((line, index) => {
        if (!line.trim()) return <span className="rich-gap" key={index} />;
        if (looksLikeMath(line)) {
          return <code className="math-line" dir="ltr" key={index}>{line.trim()}</code>;
        }
        return <p dir="auto" key={index}>{line.trim()}</p>;
      })}
    </div>
  );
}

function scoreStatus(total: number, maximum: number): string {
  if (maximum <= 0) return "نامشخص";
  const ratio = total / maximum;
  if (ratio >= 0.9) return "کامل";
  if (ratio >= 0.7) return "قابل قبول";
  if (ratio >= 0.4) return "نیازمند اصلاح";
  return "ضعیف";
}

type GradingViewProps = {
  data: Record<string, unknown>;
  evidenceCount: number;
  onSaveMistake?: (mistake: MistakeInput) => void | Promise<void>;
};

function GradingView({ data, evidenceCount, onSaveMistake }: GradingViewProps) {
  const breakdown = asArray(data.score_breakdown).map(asRecord);
  const missing = asArray(data.missing_steps).map(asRecord);
  const range = asRecord(data.likely_professor_score);
  const suggestedMistake = asRecord(data.suggested_mistake);
  const totalScore = numberValue(data.total_score);
  const maxScore = numberValue(data.max_score);
  const fullScore = maxScore > 0 && Math.abs(totalScore - maxScore) < 0.01;
  const strengths = asArray(data.strengths).map(text).filter(Boolean);
  const scientificErrors = asArray(data.scientific_errors).map(text).filter(Boolean);
  const calculationErrors = asArray(data.calculation_errors).map(text).filter(Boolean);
  const notationErrors = asArray(data.notation_errors).map(text).filter(Boolean);
  const combinedErrors = [...scientificErrors, ...calculationErrors, ...notationErrors];

  const saveableMistake: MistakeInput | null = text(suggestedMistake.description)
    ? {
        topic: text(suggestedMistake.topic),
        category: text(suggestedMistake.category),
        description: text(suggestedMistake.description),
        prevention: text(suggestedMistake.prevention),
        severity: (["low", "medium", "high"].includes(text(suggestedMistake.severity))
          ? text(suggestedMistake.severity)
          : "medium") as MistakeInput["severity"],
      }
    : null;

  return (
    <div className="structured-view">
      <div className="score-hero">
        <div className="primary-score"><span>نمره پیشنهادی</span><strong>{text(data.total_score)} <small>از {text(data.max_score)}</small></strong></div>
        <div><span>وضعیت پاسخ</span><strong className="score-status">{scoreStatus(totalScore, maxScore)}</strong></div>
        <div><span>پشتوانه گزارش</span><strong className="score-status">{evidenceCount > 0 ? `${Math.min(evidenceCount, 3)} شاهد مرتبط` : "بدون شاهد مستقیم"}</strong></div>
        {Object.keys(range).length > 0 && <div><span>تخمین استاد</span><strong>{text(range.minimum)} تا {text(range.maximum)}</strong></div>}
      </div>

      <section className="rubric-section">
        <div className="section-title-row"><h4>ریز نمره</h4><span>{breakdown.length} معیار</span></div>
        <div className="rubric-cards">
          {breakdown.map((item, index) => (
            <article className="rubric-card" key={index}>
              <div className="rubric-card-head">
                <strong>{text(item.criterion)}</strong>
                <span>{text(item.awarded_score)} از {text(item.max_score)}</span>
              </div>
              <p dir="auto">{text(item.rationale)}</p>
            </article>
          ))}
        </div>
      </section>

      {text(data.first_divergence) && <section className="result-section warning-section"><h4>اولین نقطه انحراف</h4><RichText value={text(data.first_divergence)} compact /></section>}

      {strengths.length > 0 && <section className="result-section success-section"><h4>نقاط قوت</h4><ul>{strengths.map((item, index) => <li dir="auto" key={index}>{item}</li>)}</ul></section>}

      {combinedErrors.length > 0 && <section className="result-section danger-section"><h4>خطاهای اصلی</h4><ul>{combinedErrors.map((item, index) => <li dir="auto" key={index}>{item}</li>)}</ul></section>}

      {missing.length > 0 && <section className="result-section"><h4>مراحل ازدست‌رفته</h4><div className="result-list">{missing.map((item, index) => <article key={index}><strong>{text(item.step)}</strong><p dir="auto">{text(item.impact)}</p><small dir="auto">{text(item.suggested_fix)}</small></article>)}</div></section>}

      {saveableMistake && onSaveMistake && (
        <section className="mistake-suggestion">
          <div><strong>این خطا را برای تمرین‌های بعدی نگه دار</strong><p>{saveableMistake.description}</p></div>
          <button className="button secondary" type="button" onClick={() => void onSaveMistake(saveableMistake)}>ثبت در دفترچه خطا</button>
        </section>
      )}

      {text(data.corrected_answer) && (
        <details className="result-details" open={!fullScore}>
          <summary>{fullScore ? "نمایش راه‌حل مرجع" : "پاسخ اصلاح‌شده"}</summary>
          <RichText value={text(data.corrected_answer)} />
        </details>
      )}
    </div>
  );
}

function ProfileView({ data }: { data: Record<string, unknown> }) {
  const claims = asArray(data.claims).map(asRecord);
  return (
    <div className="structured-view">
      <div className="score-hero compact"><div><span>شواهد استفاده‌شده</span><strong>{text(data.evidence_count)}</strong></div><div><span>وضعیت پروفایل</span><strong className="score-status">{claims.length > 1 ? "در حال شکل‌گیری" : "داده ناکافی"}</strong></div></div>
      <div className="claim-grid">{claims.map((claim, index) => <article className="claim-card" key={index}><div><span className={`status-pill ${text(claim.status)}`}>{text(claim.status)}</span></div><h4>{text(claim.category)}</h4><p dir="auto">{text(claim.claim)}</p><span>{asArray(claim.evidence_refs).length} ارجاع</span></article>)}</div>
      {asArray(data.recommended_exam_strategy).length > 0 && <section className="result-section"><h4>راهبرد پیشنهادی</h4><ul>{asArray(data.recommended_exam_strategy).map((item, index) => <li dir="auto" key={index}>{text(item)}</li>)}</ul></section>}
    </div>
  );
}

function PlanView({ data }: { data: Record<string, unknown> }) {
  const days = asArray(data.days).map(asRecord);
  return (
    <div className="structured-view">
      <div className="score-hero compact"><div><span>مدت برنامه</span><strong>{text(data.duration_days)} روز</strong></div><div><span>زمان روزانه</span><strong>{text(data.daily_minutes)} دقیقه</strong></div></div>
      <div className="plan-list">{days.map((day, index) => <article className="plan-day" key={index}><div className="day-number">{text(day.day_number)}</div><div><h4>{text(day.focus)}</h4>{asArray(day.tasks).map((taskValue, taskIndex) => { const task = asRecord(taskValue); return <div className="plan-task" key={taskIndex}><strong>{text(task.title)}</strong><span>{text(task.estimated_minutes)} دقیقه</span><small>{text(task.completion_criteria)}</small></div>; })}</div></article>)}</div>
    </div>
  );
}

type StructuredOutputProps = {
  response: CoachResponse;
  onSaveMistake?: (mistake: MistakeInput) => void | Promise<void>;
};

export function StructuredOutput({ response, onSaveMistake }: StructuredOutputProps) {
  const data = asRecord(response.structured_output);
  if (!response.structured_output || !response.schema) {
    return <pre className="plain-output" dir="auto">{response.output}</pre>;
  }
  if (response.schema === "GradingReport") return <GradingView data={data} evidenceCount={response.evidence.length} onSaveMistake={onSaveMistake} />;
  if (response.schema === "ProfessorProfile") return <ProfileView data={data} />;
  if (response.schema === "StudyPlan") return <PlanView data={data} />;
  return <pre className="plain-output">{JSON.stringify(response.structured_output, null, 2)}</pre>;
}

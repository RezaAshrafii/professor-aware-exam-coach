import type { CoachResponse } from "@/lib/types";

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

function GradingView({ data }: { data: Record<string, unknown> }) {
  const breakdown = asArray(data.score_breakdown).map(asRecord);
  const missing = asArray(data.missing_steps).map(asRecord);
  const range = asRecord(data.likely_professor_score);
  return (
    <div className="structured-view">
      <div className="score-hero">
        <div><span>نمره سخت‌گیرانه</span><strong>{text(data.total_score)} <small>از {text(data.max_score)}</small></strong></div>
        <div><span>اطمینان گزارش</span><strong>{Math.round(Number(data.confidence ?? 0) * 100)}٪</strong></div>
        {Object.keys(range).length > 0 && <div><span>بازه محتمل استاد</span><strong>{text(range.minimum)} تا {text(range.maximum)}</strong></div>}
      </div>
      <div className="table-wrap">
        <table className="score-table">
          <thead><tr><th>معیار</th><th>بارم</th><th>دریافتی</th><th>دلیل</th></tr></thead>
          <tbody>{breakdown.map((item, index) => <tr key={index}><td>{text(item.criterion)}</td><td>{text(item.max_score)}</td><td>{text(item.awarded_score)}</td><td>{text(item.rationale)}</td></tr>)}</tbody>
        </table>
      </div>
      {text(data.first_divergence) && <section className="result-section warning-section"><h4>اولین نقطه انحراف</h4><p>{text(data.first_divergence)}</p></section>}
      {missing.length > 0 && <section className="result-section"><h4>مراحل حذف‌شده</h4><div className="result-list">{missing.map((item, index) => <article key={index}><strong>{text(item.step)}</strong><p>{text(item.impact)}</p><small>{text(item.suggested_fix)}</small></article>)}</div></section>}
      {text(data.corrected_answer) && <section className="result-section answer-section"><h4>پاسخ اصلاح‌شده</h4><pre>{text(data.corrected_answer)}</pre></section>}
    </div>
  );
}

function ProfileView({ data }: { data: Record<string, unknown> }) {
  const claims = asArray(data.claims).map(asRecord);
  return (
    <div className="structured-view">
      <div className="score-hero compact"><div><span>شواهد استفاده‌شده</span><strong>{text(data.evidence_count)}</strong></div><div><span>اطمینان کلی</span><strong>{Math.round(Number(data.overall_confidence ?? 0) * 100)}٪</strong></div></div>
      <div className="claim-grid">{claims.map((claim, index) => <article className="claim-card" key={index}><div><span className={`status-pill ${text(claim.status)}`}>{text(claim.status)}</span><small>{Math.round(Number(claim.confidence ?? 0) * 100)}٪</small></div><h4>{text(claim.category)}</h4><p>{text(claim.claim)}</p><span>{asArray(claim.evidence_refs).length} ارجاع</span></article>)}</div>
      {asArray(data.recommended_exam_strategy).length > 0 && <section className="result-section"><h4>راهبرد پیشنهادی</h4><ul>{asArray(data.recommended_exam_strategy).map((item, index) => <li key={index}>{text(item)}</li>)}</ul></section>}
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

export function StructuredOutput({ response }: { response: CoachResponse }) {
  const data = asRecord(response.structured_output);
  if (!response.structured_output || !response.schema) {
    return <pre className="plain-output">{response.output}</pre>;
  }
  if (response.schema === "GradingReport") return <GradingView data={data} />;
  if (response.schema === "ProfessorProfile") return <ProfileView data={data} />;
  if (response.schema === "StudyPlan") return <PlanView data={data} />;
  return <pre className="plain-output">{JSON.stringify(response.structured_output, null, 2)}</pre>;
}

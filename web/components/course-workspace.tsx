"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { Icons } from "@/components/icons";
import { StructuredOutput } from "@/components/structured-output";
import { api } from "@/lib/api";
import type { CoachResponse, CourseInput, ExampleCardInput, MistakeInput, Workspace } from "@/lib/types";

type Tab = "overview" | "sources" | "examples" | "coach" | "history" | "mistakes" | "settings";

const tabs: Array<{ id: Tab; label: string; icon: keyof typeof Icons }> = [
  { id: "overview", label: "نمای کلی", icon: "Home" },
  { id: "sources", label: "منابع", icon: "File" },
  { id: "examples", label: "مثال‌های استاد", icon: "Layers" },
  { id: "coach", label: "مربی پاسخ", icon: "Sparkles" },
  { id: "history", label: "تاریخچه", icon: "History" },
  { id: "mistakes", label: "دفترچه خطا", icon: "Alert" },
  { id: "settings", label: "تنظیمات", icon: "Settings" },
];

const emptyExample: ExampleCardInput = {
  title: "", topic: "", question: "", solution: "", method_name: "",
  source_kind: "cleaned_transcript", source_reference: "", notes: "", status: "draft",
};
const emptyMistake: MistakeInput = { topic: "", category: "", description: "", prevention: "", severity: "medium" };

function courseInput(workspace: Workspace): CourseInput {
  const course = workspace.course;
  return {
    name: course.name, professor: course.professor, term: course.term, exam_date: course.exam_date,
    target_grade: course.target_grade, daily_minutes: course.daily_minutes, exam_scope: course.exam_scope, notes: course.notes,
  };
}

function humanBytes(characters: number) {
  if (characters < 1000) return `${characters} نویسه`;
  return `${(characters / 1000).toFixed(1)} هزار نویسه`;
}

export function CourseWorkspace({ courseId }: { courseId: number }) {
  const router = useRouter();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [example, setExample] = useState<ExampleCardInput>(emptyExample);
  const [mistake, setMistake] = useState<MistakeInput>(emptyMistake);
  const [coachMode, setCoachMode] = useState("grade");
  const [coachPrompt, setCoachPrompt] = useState("");
  const [coachResponse, setCoachResponse] = useState<CoachResponse | null>(null);
  const [courseForm, setCourseForm] = useState<CourseInput | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);

  async function load(silent = false) {
    if (!silent) setLoading(true);
    setError("");
    try {
      const data = await api.getWorkspace(courseId);
      setWorkspace(data);
      setCourseForm(courseInput(data));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "فضای درس بارگذاری نشد.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, [courseId]);

  function flash(message: string) {
    setNotice(message);
    window.setTimeout(() => setNotice(""), 2600);
  }

  const confirmedExamples = useMemo(() => workspace?.example_cards.filter((item) => item.status === "confirmed").length ?? 0, [workspace]);

  async function uploadSource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    setBusy(true); setError("");
    try { await api.uploadSource(courseId, file); if (fileRef.current) fileRef.current.value = ""; await load(true); flash("منبع پردازش و اضافه شد."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "بارگذاری ناموفق بود."); }
    finally { setBusy(false); }
  }

  async function createExample(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    try { await api.createExample(courseId, example); setExample(emptyExample); await load(true); flash("کارت مثال ذخیره شد."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "ذخیره مثال ناموفق بود."); }
    finally { setBusy(false); }
  }

  async function createMistake(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    try { await api.createMistake(courseId, mistake); setMistake(emptyMistake); await load(true); flash("خطا ثبت شد."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "ثبت خطا ناموفق بود."); }
    finally { setBusy(false); }
  }

  async function runCoach(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setCoachResponse(null);
    try { const response = await api.runCoach(courseId, coachMode, coachPrompt); setCoachResponse(response); await load(true); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "اجرای مربی ناموفق بود."); }
    finally { setBusy(false); }
  }

  async function updateCourse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!courseForm) return; setBusy(true); setError("");
    try { await api.updateCourse(courseId, courseForm); await load(true); flash("اطلاعات درس ذخیره شد."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "ذخیره تنظیمات ناموفق بود."); }
    finally { setBusy(false); }
  }

  if (loading) return <main className="workspace-loading"><div className="loading-mark"><Icons.Book /></div><p>در حال آماده‌کردن فضای درس…</p></main>;
  if (!workspace) return <main className="workspace-loading"><div className="alert error"><Icons.Alert />{error || "درس پیدا نشد."}</div><Link className="button secondary" href="/">بازگشت به داشبورد</Link></main>;

  const course = workspace.course;

  return (
    <main className="workspace-shell">
      <aside className={`workspace-sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-brand"><div className="brand-mark"><Icons.Book /></div><div><strong>Exam Coach</strong><span>فضای درس</span></div></div>
        <div className="course-identity"><span className="course-kicker">{course.term || "ترم ثبت نشده"}</span><h1>{course.name}</h1><p>{course.professor || "استاد ثبت نشده"}</p></div>
        <nav className="workspace-nav">{tabs.map((item) => { const Icon = Icons[item.icon]; return <button key={item.id} className={tab === item.id ? "active" : ""} onClick={() => { setTab(item.id); setSidebarOpen(false); }}><Icon /><span>{item.label}</span>{item.id === "sources" && <small>{workspace.sources.length}</small>}{item.id === "examples" && <small>{workspace.example_cards.length}</small>}{item.id === "mistakes" && <small>{workspace.mistakes.length}</small>}</button>; })}</nav>
        <div className="sidebar-footer"><Link href="/"><Icons.ArrowLeft /> بازگشت به همه درس‌ها</Link><Link className="model-chip-link" href="/settings"><div className={`model-chip ${workspace.model_enabled ? "enabled" : "demo"}`}><span />{workspace.model_enabled ? (workspace.active_provider || "مدل واقعی فعال") : "اتصال مدل"}</div></Link></div>
      </aside>
      {sidebarOpen && <button className="mobile-backdrop" onClick={() => setSidebarOpen(false)} aria-label="بستن منو" />}

      <section className="workspace-main">
        <header className="workspace-header">
          <button className="menu-button" onClick={() => setSidebarOpen(true)}><Icons.Menu /></button>
          <div><span className="eyebrow">{tabs.find((item) => item.id === tab)?.label}</span><h2>{course.name}</h2></div>
          <div className="header-actions"><button className="icon-button" title="تازه‌سازی" onClick={() => void load()}><Icons.Refresh /></button>{course.target_grade !== null && <span className="target-badge large">هدف {course.target_grade}</span>}</div>
        </header>

        <div className="workspace-content">
          {error && <div className="alert error"><Icons.Alert />{error}<button onClick={() => setError("")}><Icons.X /></button></div>}
          {notice && <div className="toast-success"><Icons.Check />{notice}</div>}

          {tab === "overview" && <div className="workspace-grid overview-grid">
            <section className="panel hero-panel"><div><span className="eyebrow">وضعیت آماده‌سازی</span><h3>{confirmedExamples ? "روش‌های استاد در حال شکل‌گیری است" : "ثبت شواهد کلاس را شروع کن"}</h3><p>{confirmedExamples ? `${confirmedExamples} مثال تأییدشده اکنون در پاسخ‌ها قابل استفاده است.` : "مثال‌های حل‌شده استاد را وارد کن تا پاسخ‌ها فقط بر پایه روش‌های واقعی کلاس ساخته شوند."}</p><button className="button primary" onClick={() => setTab("examples")}><Icons.Plus /> افزودن مثال استاد</button></div><div className="readiness-ring"><strong>{Math.min(100, workspace.sources.length * 12 + confirmedExamples * 18)}</strong><span>آمادگی داده</span></div></section>
            <section className="metric-row"><article><Icons.File /><div><strong>{workspace.sources.length}</strong><span>منبع</span></div></article><article><Icons.Layers /><div><strong>{confirmedExamples}</strong><span>مثال تأییدشده</span></div></article><article><Icons.History /><div><strong>{workspace.runs.length}</strong><span>اجرای ذخیره‌شده</span></div></article><article><Icons.Alert /><div><strong>{workspace.mistakes.length}</strong><span>خطای ثبت‌شده</span></div></article></section>
            <section className="panel span-two"><div className="panel-heading"><div><span className="eyebrow">شروع سریع</span><h3>قدم بعدی پیشنهادی</h3></div></div><div className="quick-actions"><button onClick={() => setTab("sources")}><span>۱</span><div><strong>منابع درس را کامل کن</strong><small>جزوه، متن تمیزشده و فایل‌های قابل انتخاب</small></div><Icons.ArrowLeft /></button><button onClick={() => setTab("examples")}><span>۲</span><div><strong>مثال‌های کلاس را تأیید کن</strong><small>فقط مواردی که با منبع اصلی تطبیق داده‌ای</small></div><Icons.ArrowLeft /></button><button onClick={() => setTab("coach")}><span>۳</span><div><strong>یک پاسخ را سخت‌گیرانه بررسی کن</strong><small>سؤال و پاسخ خودت را وارد حالت تصحیح کن</small></div><Icons.ArrowLeft /></button></div></section>
            <section className="panel"><div className="panel-heading"><div><span className="eyebrow">درس</span><h3>اطلاعات کلیدی</h3></div></div><dl className="info-list"><div><dt>استاد</dt><dd>{course.professor || "—"}</dd></div><div><dt>تاریخ امتحان</dt><dd>{course.exam_date || "—"}</dd></div><div><dt>زمان روزانه</dt><dd>{course.daily_minutes} دقیقه</dd></div><div><dt>محدوده</dt><dd>{course.exam_scope || "هنوز ثبت نشده"}</dd></div></dl></section>
          </div>}

          {tab === "sources" && <div className="workspace-grid sources-grid">
            <section className="panel span-two"><div className="panel-heading"><div><span className="eyebrow">Knowledge Base</span><h3>منابع درس</h3><p>فایل‌های متنی قابل استخراج در retrieval استفاده می‌شوند.</p></div><span className="count-badge">{workspace.sources.length}</span></div>{workspace.sources.length ? <div className="source-list">{workspace.sources.map((source) => <article key={source.id}><div className="file-icon"><Icons.File /></div><div><strong>{source.filename}</strong><span>{source.source_type.toUpperCase()} · {humanBytes(source.character_count)}</span></div><button className="icon-button danger" onClick={async () => { if (!confirm("این منبع حذف شود؟")) return; await api.deleteSource(source.id); await load(true); }}><Icons.Trash /></button></article>)}</div> : <div className="empty-state"><Icons.File /><h4>هنوز منبعی اضافه نشده</h4><p>برای شروع یک PDF متنی، DOCX، TXT یا Markdown اضافه کن.</p></div>}</section>
            <section className="panel upload-card"><div className="panel-heading"><div><span className="eyebrow">افزودن منبع</span><h3>بارگذاری فایل</h3></div></div><form onSubmit={uploadSource} className="form-stack"><label className="dropzone"><Icons.Upload /><strong>فایل را انتخاب کن</strong><span>PDF، DOCX، TXT یا MD تا ۲۰ مگابایت</span><input ref={fileRef} type="file" required accept=".pdf,.docx,.txt,.md" /></label><button className="button primary full" disabled={busy}>{busy ? "در حال پردازش…" : "بارگذاری و پردازش"}</button></form><div className="micro-note">PDF اسکن‌شده فعلاً OCR نمی‌شود؛ متن تمیزشده را می‌توانی به‌صورت TXT یا DOCX وارد کنی.</div></section>
          </div>}

          {tab === "examples" && <div className="workspace-grid example-grid">
            <section className="panel span-two"><div className="panel-heading"><div><span className="eyebrow">شواهد تدریس</span><h3>مثال‌های ثبت‌شده استاد</h3><p>کارت پیش‌نویس هرگز وارد پاسخ مدل نمی‌شود.</p></div><span className="count-badge">{workspace.example_cards.length}</span></div>{workspace.example_cards.length ? <div className="example-list">{workspace.example_cards.map((card) => <article key={card.id} className={`example-item ${card.status}`}><div className="example-item-head"><div><span className={`status-pill ${card.status}`}>{card.status === "confirmed" ? "تأییدشده" : "پیش‌نویس"}</span>{card.topic && <span className="subtle-pill">{card.topic}</span>}</div><div><button className="button tiny" onClick={async () => { await api.setExampleStatus(courseId, card.id, card.status === "confirmed" ? "draft" : "confirmed"); await load(true); }}>{card.status === "confirmed" ? "بازگشت به پیش‌نویس" : "تأیید"}</button><button className="icon-button danger" onClick={async () => { if (!confirm("این کارت حذف شود؟")) return; await api.deleteExample(courseId, card.id); await load(true); }}><Icons.Trash /></button></div></div><h4>{card.title}</h4><div className="example-meta"><span>روش: {card.method_name || "ثبت نشده"}</span><span>مرجع: {card.source_reference || "—"}</span></div><details><summary>مشاهده سؤال و راه‌حل</summary><div className="detail-content"><strong>صورت سؤال</strong><p>{card.question}</p><strong>راه‌حل استاد</strong><pre>{card.solution}</pre>{card.notes && <><strong>یادداشت</strong><p>{card.notes}</p></>}</div></details></article>)}</div> : <div className="empty-state"><Icons.Layers /><h4>هنوز مثال کلاسی نداری</h4><p>متن تمیزشده از روی جزوه، تخته یا ویدئو را در فرم روبه‌رو ثبت کن.</p></div>}</section>
            <section className="panel sticky-panel"><div className="panel-heading"><div><span className="eyebrow">کارت جدید</span><h3>افزودن مثال</h3></div></div><form className="form-stack" onSubmit={createExample}><label className="field"><span>عنوان *</span><input required value={example.title} onChange={(e) => setExample({ ...example, title: e.target.value })} placeholder="مثال بیز جلسه چهارم" /></label><div className="form-grid"><label className="field"><span>مبحث</span><input value={example.topic} onChange={(e) => setExample({ ...example, topic: e.target.value })} /></label><label className="field"><span>نام روش</span><input value={example.method_name} onChange={(e) => setExample({ ...example, method_name: e.target.value })} /></label></div><label className="field"><span>نوع منبع</span><select value={example.source_kind} onChange={(e) => setExample({ ...example, source_kind: e.target.value })}><option value="cleaned_transcript">متن تمیزشده</option><option value="class_note">یادداشت کلاس</option><option value="board_photo">عکس تخته</option><option value="video_clip">بخش ویدئو</option><option value="other">سایر</option></select></label><label className="field"><span>مرجع</span><input value={example.source_reference} onChange={(e) => setExample({ ...example, source_reference: e.target.value })} placeholder="صفحه ۱۲ یا 00:18:40" /></label><label className="field"><span>صورت سؤال *</span><textarea required rows={4} value={example.question} onChange={(e) => setExample({ ...example, question: e.target.value })} /></label><label className="field"><span>راه‌حل استاد *</span><textarea required rows={8} value={example.solution} onChange={(e) => setExample({ ...example, solution: e.target.value })} /></label><label className="field"><span>یادداشت</span><textarea rows={3} value={example.notes} onChange={(e) => setExample({ ...example, notes: e.target.value })} /></label><label className="field"><span>وضعیت</span><select value={example.status} onChange={(e) => setExample({ ...example, status: e.target.value as "draft" | "confirmed" })}><option value="draft">پیش‌نویس؛ وارد مدل نشود</option><option value="confirmed">تأییدشده</option></select></label><button className="button primary full" disabled={busy}>ذخیره کارت مثال</button></form></section>
          </div>}

          {tab === "coach" && <div className="workspace-grid coach-grid">
            <section className="panel coach-form-panel"><div className="panel-heading"><div><span className="eyebrow">AI Workspace</span><h3>مربی پاسخ</h3><p>برای تصحیح، صورت سؤال، پاسخ خودت و بارم را کامل وارد کن.</p></div></div><form className="form-stack" onSubmit={runCoach}><label className="field"><span>حالت</span><select value={coachMode} onChange={(e) => setCoachMode(e.target.value)}><option value="grade">تصحیح سخت‌گیرانه</option><option value="profile">پروفایل استاد</option><option value="analyze">تحلیل منابع</option><option value="teach">آموزش مبحث</option><option value="guided">تمرین هدایت‌شده</option><option value="exam_answer">نسخه برگه امتحان</option><option value="oral">دفاع شفاهی</option><option value="plan">برنامه مطالعه</option></select></label><label className="field"><span>درخواست *</span><textarea required rows={14} value={coachPrompt} onChange={(e) => setCoachPrompt(e.target.value)} placeholder={coachMode === "grade" ? "صورت سؤال:\n...\n\nپاسخ من:\n...\n\nبارم: ۱۰" : "درخواستت را دقیق بنویس…"} /></label><button className="button primary full large" disabled={busy}>{busy ? "در حال بررسی…" : "اجرای تحلیل"}</button></form><div className="micro-note">فقط مثال‌های تأییدشده و chunkهای بازیابی‌شده به مدل داده می‌شوند.</div></section>
            <section className="panel result-panel"><div className="panel-heading"><div><span className="eyebrow">خروجی</span><h3>نتیجه تحلیل</h3></div>{coachResponse && <span className={`validation-badge ${coachResponse.validation_status ?? "not_applicable"}`}>{coachResponse.validation_status === "valid" ? "معتبر" : coachResponse.validation_status === "recovered" ? "اصلاح‌شده" : coachResponse.validation_status === "invalid_fallback" ? "نامعتبر" : coachResponse.provider}</span>}</div>{coachResponse ? <><StructuredOutput response={coachResponse} />{coachResponse.validation_error && <div className="alert warning"><Icons.Alert />{coachResponse.validation_error}</div>}{coachResponse.evidence.length > 0 && <div className="evidence-list"><h4>شواهد استفاده‌شده</h4>{coachResponse.evidence.map((item, index) => <article key={index}><span>{index + 1}</span><div><strong>{item.filename}</strong><small>{item.chunk_index === null ? "کارت مثال استاد" : `قطعه ${item.chunk_index}`}</small></div></article>)}</div>}</> : <div className="empty-state result-empty"><Icons.Sparkles /><h4>هنوز تحلیلی اجرا نشده</h4><p>حالت مناسب را انتخاب کن و سؤال یا پاسخ خودت را وارد کن.</p></div>}</section>
          </div>}

          {tab === "history" && <section className="panel"><div className="panel-heading"><div><span className="eyebrow">Run Log</span><h3>تاریخچه اجراها</h3></div><span className="count-badge">{workspace.runs.length}</span></div>{workspace.runs.length ? <div className="history-list">{workspace.runs.map((run) => <details key={run.id}><summary><div><span className="subtle-pill">{run.mode}</span><strong>{run.user_input.slice(0, 100)}{run.user_input.length > 100 ? "…" : ""}</strong></div><small>{run.created_at} · {run.provider}</small></summary><pre>{run.output}</pre></details>)}</div> : <div className="empty-state"><Icons.History /><h4>تاریخچه خالی است</h4><p>هر بار که مربی را اجرا کنی، خروجی اینجا ذخیره می‌شود.</p></div>}</section>}

          {tab === "mistakes" && <div className="workspace-grid mistake-grid">
            <section className="panel span-two"><div className="panel-heading"><div><span className="eyebrow">Error Log</span><h3>خطاهای ثبت‌شده</h3></div><span className="count-badge">{workspace.mistakes.length}</span></div>{workspace.mistakes.length ? <div className="mistake-list">{workspace.mistakes.map((item) => <article key={item.id} className={`mistake-item ${item.severity}`}><div><span className="subtle-pill">{item.category || "بدون دسته"}</span><strong>{item.topic || "موضوع نامشخص"}</strong></div><p>{item.description}</p>{item.prevention && <small>راه جلوگیری: {item.prevention}</small>}<button className="icon-button danger" onClick={async () => { await api.deleteMistake(courseId, item.id); await load(true); }}><Icons.Trash /></button></article>)}</div> : <div className="empty-state"><Icons.Alert /><h4>خطایی ثبت نشده</h4><p>خطاهای پرتکرار را ثبت کن تا در تمرین‌های بعدی فراموش نشوند.</p></div>}</section>
            <section className="panel sticky-panel"><div className="panel-heading"><div><span className="eyebrow">خطای جدید</span><h3>ثبت دستی</h3></div></div><form className="form-stack" onSubmit={createMistake}><label className="field"><span>مبحث</span><input value={mistake.topic} onChange={(e) => setMistake({ ...mistake, topic: e.target.value })} /></label><label className="field"><span>دسته</span><input value={mistake.category} onChange={(e) => setMistake({ ...mistake, category: e.target.value })} placeholder="مفهومی، محاسبات، نمادگذاری…" /></label><label className="field"><span>شرح خطا *</span><textarea required rows={5} value={mistake.description} onChange={(e) => setMistake({ ...mistake, description: e.target.value })} /></label><label className="field"><span>راه جلوگیری</span><textarea rows={3} value={mistake.prevention} onChange={(e) => setMistake({ ...mistake, prevention: e.target.value })} /></label><label className="field"><span>شدت</span><select value={mistake.severity} onChange={(e) => setMistake({ ...mistake, severity: e.target.value as MistakeInput["severity"] })}><option value="low">کم</option><option value="medium">متوسط</option><option value="high">زیاد</option></select></label><button className="button primary full" disabled={busy}>ثبت خطا</button></form></section>
          </div>}

          {tab === "settings" && courseForm && <div className="workspace-grid settings-grid"><section className="panel span-two model-settings-shortcut"><div><span className="eyebrow">مدل فعال</span><h3>{workspace.active_provider || "مدلی فعال نیست"}</h3><p>کلید API و مدل انتخابی برای تمام درس‌ها مشترک است.</p></div><Link className="button secondary" href="/settings"><Icons.Settings /> تنظیم مدل و API</Link></section><section className="panel span-two"><div className="panel-heading"><div><span className="eyebrow">Course Settings</span><h3>اطلاعات درس</h3></div></div><form className="form-stack" onSubmit={updateCourse}><div className="form-grid"><label className="field"><span>نام درس *</span><input required value={courseForm.name} onChange={(e) => setCourseForm({ ...courseForm, name: e.target.value })} /></label><label className="field"><span>استاد</span><input value={courseForm.professor} onChange={(e) => setCourseForm({ ...courseForm, professor: e.target.value })} /></label><label className="field"><span>ترم</span><input value={courseForm.term} onChange={(e) => setCourseForm({ ...courseForm, term: e.target.value })} /></label><label className="field"><span>تاریخ امتحان</span><input type="date" value={courseForm.exam_date} onChange={(e) => setCourseForm({ ...courseForm, exam_date: e.target.value })} /></label><label className="field"><span>نمره هدف</span><input type="number" min="0" max="20" step="0.25" value={courseForm.target_grade ?? ""} onChange={(e) => setCourseForm({ ...courseForm, target_grade: e.target.value ? Number(e.target.value) : null })} /></label><label className="field"><span>زمان روزانه</span><input type="number" min="10" max="720" value={courseForm.daily_minutes} onChange={(e) => setCourseForm({ ...courseForm, daily_minutes: Number(e.target.value) })} /></label></div><label className="field"><span>محدوده امتحان</span><textarea rows={4} value={courseForm.exam_scope} onChange={(e) => setCourseForm({ ...courseForm, exam_scope: e.target.value })} /></label><label className="field"><span>یادداشت</span><textarea rows={4} value={courseForm.notes} onChange={(e) => setCourseForm({ ...courseForm, notes: e.target.value })} /></label><button className="button primary" disabled={busy}>ذخیره تغییرات</button></form></section><section className="panel danger-zone"><div><span className="eyebrow">Danger Zone</span><h3>حذف کامل درس</h3><p>درس، منابع، مثال‌ها، تاریخچه و خطاهای آن برای همیشه حذف می‌شوند.</p></div><button className="button danger" onClick={async () => { if (!confirm("این درس و تمام اطلاعاتش برای همیشه حذف شود؟")) return; await api.deleteCourse(courseId); router.push("/"); }}>حذف درس</button></section></div>}
        </div>
      </section>
    </main>
  );
}

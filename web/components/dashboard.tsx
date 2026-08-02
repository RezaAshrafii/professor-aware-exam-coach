"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { Icons } from "@/components/icons";
import { api } from "@/lib/api";
import type { CourseInput, CourseSummary } from "@/lib/types";

const emptyCourse: CourseInput = {
  name: "",
  professor: "",
  term: "",
  exam_date: "",
  target_grade: 18,
  daily_minutes: 90,
  exam_scope: "",
  notes: "",
};

function formatDate(value: string) {
  if (!value) return "تاریخ مشخص نشده";
  try {
    return new Intl.DateTimeFormat("fa-IR", { dateStyle: "medium" }).format(new Date(value));
  } catch {
    return value;
  }
}

export function Dashboard() {
  const [courses, setCourses] = useState<CourseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [backendReady, setBackendReady] = useState<boolean | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<CourseInput>(emptyCourse);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    const healthy = await api.health();
    setBackendReady(healthy);
    if (!healthy) {
      setLoading(false);
      return;
    }
    try {
      setCourses(await api.listCourses());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "بارگذاری درس‌ها ناموفق بود.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const totals = useMemo(
    () => ({
      courses: courses.length,
      sources: courses.reduce((sum, course) => sum + course.source_count, 0),
      examples: courses.reduce((sum, course) => sum + course.example_count, 0),
      runs: courses.reduce((sum, course) => sum + course.run_count, 0),
    }),
    [courses],
  );

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const course = await api.createCourse(form);
      window.location.href = `/courses/${course.id}`;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "ساخت درس ناموفق بود.");
      setSaving(false);
    }
  }

  return (
    <main className="page-shell dashboard-page">
      <header className="topbar container-wide">
        <div className="brand-lockup">
          <div className="brand-mark"><Icons.Book /></div>
          <div>
            <strong>Exam Coach</strong>
            <span>آمادگی استادمحور برای امتحان</span>
          </div>
        </div>
        <div className="topbar-actions">
          <span className="version-label">v0.6</span>
          <div className={`connection ${backendReady ? "online" : backendReady === false ? "offline" : "checking"}`}>
            <span className="connection-dot" />
            {backendReady ? "هسته متصل است" : backendReady === false ? "هسته در دسترس نیست" : "در حال بررسی"}
          </div>
        </div>
      </header>

      <section className="hero container-wide">
        <div className="hero-copy">
          <span className="eyebrow">فضای مطالعه شخصی</span>
          <h1>هر درس، یک فضای منظم برای منابع، روش استاد و تمرین دقیق.</h1>
          <p>
            جزوه‌ها و مثال‌های کلاس را ثبت کن، پاسخ‌ها را با شواهد همان درس بررسی کن و خطاهای پرتکرار را یک‌جا نگه دار.
          </p>
          <div className="hero-actions">
            <button className="button primary large" onClick={() => setModalOpen(true)} disabled={!backendReady}>
              <Icons.Plus /> ساخت درس جدید
            </button>
            <button className="button secondary large" onClick={() => void load()}>
              <Icons.Refresh /> تازه‌سازی
            </button>
          </div>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="visual-orbit orbit-one" />
          <div className="visual-orbit orbit-two" />
          <div className="visual-card visual-card-main">
            <div className="visual-card-icon"><Icons.Sparkles /></div>
            <span>پاسخ تحت شواهد</span>
            <strong>روش‌های تأییدشده استاد</strong>
            <div className="visual-progress"><i /></div>
          </div>
          <div className="visual-card visual-card-small top"><Icons.Check /><span>ارجاع معتبر</span></div>
          <div className="visual-card visual-card-small bottom"><Icons.Layers /><span>مثال‌های کلاس</span></div>
        </div>
      </section>

      <section className="stats-grid container-wide">
        <div className="stat-card"><span>درس‌ها</span><strong>{totals.courses}</strong><small>workspace فعال</small></div>
        <div className="stat-card"><span>منابع</span><strong>{totals.sources}</strong><small>فایل پردازش‌شده</small></div>
        <div className="stat-card"><span>مثال‌ها</span><strong>{totals.examples}</strong><small>کارت ثبت‌شده</small></div>
        <div className="stat-card"><span>اجراها</span><strong>{totals.runs}</strong><small>تحلیل ذخیره‌شده</small></div>
      </section>

      <section className="content-section container-wide">
        <div className="section-heading">
          <div><span className="eyebrow">درس‌های من</span><h2>فضاهای فعال</h2></div>
          <button className="button primary" onClick={() => setModalOpen(true)} disabled={!backendReady}><Icons.Plus /> درس جدید</button>
        </div>

        {error && <div className="alert error"><Icons.Alert />{error}</div>}
        {backendReady === false && (
          <div className="empty-state prominent">
            <div className="empty-icon"><Icons.Alert /></div>
            <h3>ابتدا backend را اجرا کن</h3>
            <p>فایل <code>start_product_windows.bat</code> یا <code>start_product_unix.sh</code> هر دو بخش برنامه را بالا می‌آورد.</p>
          </div>
        )}
        {loading ? (
          <div className="course-grid">{[1, 2, 3].map((item) => <div className="course-card skeleton" key={item} />)}</div>
        ) : courses.length ? (
          <div className="course-grid">
            {courses.map((course) => (
              <Link className="course-card" href={`/courses/${course.id}`} key={course.id}>
                <div className="course-card-top">
                  <div className="course-icon"><Icons.Book /></div>
                  <span className="course-arrow"><Icons.ArrowLeft /></span>
                </div>
                <div className="course-card-title">
                  <h3>{course.name}</h3>
                  <p>{course.professor || "استاد ثبت نشده"}{course.term ? ` · ${course.term}` : ""}</p>
                </div>
                <div className="course-meta-row">
                  <span><Icons.Clock /> {formatDate(course.exam_date)}</span>
                  {course.target_grade !== null && <span className="target-badge">هدف {course.target_grade}</span>}
                </div>
                <div className="course-card-stats">
                  <span><strong>{course.source_count}</strong> منبع</span>
                  <span><strong>{course.example_count}</strong> مثال</span>
                  <span><strong>{course.mistake_count}</strong> خطا</span>
                </div>
              </Link>
            ))}
          </div>
        ) : backendReady ? (
          <div className="empty-state prominent">
            <div className="empty-icon"><Icons.Book /></div>
            <h3>هنوز درسی نساختی</h3>
            <p>اولین درس را بساز تا منابع، مثال‌ها و تحلیل‌ها را در یک فضای جدا نگه داری.</p>
            <button className="button primary" onClick={() => setModalOpen(true)}><Icons.Plus /> ساخت اولین درس</button>
          </div>
        ) : null}
      </section>

      {modalOpen && (
        <div className="modal-layer" role="dialog" aria-modal="true">
          <button className="modal-backdrop" aria-label="بستن" onClick={() => setModalOpen(false)} />
          <div className="modal-card">
            <div className="modal-heading">
              <div><span className="eyebrow">Workspace جدید</span><h2>ساخت درس</h2></div>
              <button className="icon-button" onClick={() => setModalOpen(false)}><Icons.X /></button>
            </div>
            <form className="form-stack" onSubmit={submit}>
              <label className="field"><span>نام درس *</span><input autoFocus required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="مثلاً احتمال ۲" /></label>
              <div className="form-grid">
                <label className="field"><span>نام استاد</span><input value={form.professor} onChange={(event) => setForm({ ...form, professor: event.target.value })} /></label>
                <label className="field"><span>ترم</span><input value={form.term} onChange={(event) => setForm({ ...form, term: event.target.value })} placeholder="۱۴۰۵-۱" /></label>
                <label className="field"><span>تاریخ امتحان</span><input type="date" value={form.exam_date} onChange={(event) => setForm({ ...form, exam_date: event.target.value })} /></label>
                <label className="field"><span>نمره هدف</span><input type="number" min="0" max="20" step="0.25" value={form.target_grade ?? ""} onChange={(event) => setForm({ ...form, target_grade: event.target.value ? Number(event.target.value) : null })} /></label>
                <label className="field"><span>زمان روزانه</span><input type="number" min="10" max="720" value={form.daily_minutes} onChange={(event) => setForm({ ...form, daily_minutes: Number(event.target.value) })} /></label>
              </div>
              <label className="field"><span>محدوده امتحان</span><textarea rows={3} value={form.exam_scope} onChange={(event) => setForm({ ...form, exam_scope: event.target.value })} /></label>
              <div className="modal-actions">
                <button type="button" className="button secondary" onClick={() => setModalOpen(false)}>انصراف</button>
                <button className="button primary" disabled={saving}>{saving ? "در حال ساخت…" : "ساخت درس"}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}

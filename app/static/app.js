const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

function toast(message, type = "info") {
  const el = $("#toast");
  if (!el) return;
  el.textContent = message;
  el.dataset.type = type;
  el.classList.add("show");
  window.setTimeout(() => el.classList.remove("show"), 3200);
}

$$('[data-modal-open]').forEach((button) => {
  button.addEventListener('click', () => {
    const modal = document.getElementById(button.dataset.modalOpen);
    modal?.classList.add('open');
    modal?.setAttribute('aria-hidden', 'false');
  });
});

$$('[data-modal-close]').forEach((button) => {
  button.addEventListener('click', () => {
    const modal = button.closest('.modal');
    modal?.classList.remove('open');
    modal?.setAttribute('aria-hidden', 'true');
  });
});

$$('form[data-confirm]').forEach((form) => {
  form.addEventListener('submit', (event) => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  });
});

const tabRoot = $('[data-tabs]');
if (tabRoot) {
  const activateTab = (name) => {
    $$('[data-tab]', tabRoot).forEach((button) => button.classList.toggle('active', button.dataset.tab === name));
    $$('[data-panel]').forEach((panel) => panel.classList.toggle('active', panel.dataset.panel === name));
    history.replaceState(null, '', `#${name}`);
  };
  $$('[data-tab]', tabRoot).forEach((button) => button.addEventListener('click', () => activateTab(button.dataset.tab)));
  const hash = location.hash.replace('#', '');
  if ($(`[data-tab="${hash}"]`, tabRoot)) activateTab(hash);
}

const modeList = $('#mode-list');
let currentMode = 'profile';
const modeTitles = {
  profile: 'پروفایل استاد', analyze: 'تحلیل منابع', teach: 'آموزش مبحث', guided: 'تمرین هدایت‌شده',
  exam: 'آزمون شبیه‌سازی', grade: 'مصحح سخت‌گیر', exam_answer: 'نسخه برگه امتحان', oral: 'دفاع شفاهی', plan: 'برنامه امتحان'
};
if (modeList) {
  $$('.mode', modeList).forEach((button) => button.addEventListener('click', () => {
    currentMode = button.dataset.mode;
    $$('.mode', modeList).forEach((item) => item.classList.toggle('active', item === button));
    $('#mode-title').textContent = modeTitles[currentMode];
  }));
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
}

function simpleMarkdown(value) {
  let html = escapeHtml(value);
  html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>');
  html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(?:<li>.*<\/li>\n?)+/g, (match) => `<ul>${match}</ul>`);
  html = html.replace(/\n{2,}/g, '</p><p>');
  html = `<p>${html}</p>`;
  html = html.replace(/<p>\s*<(h[234]|ul)>/g, '<$1>').replace(/<\/(h[234]|ul)>\s*<\/p>/g, '</$1>');
  return html;
}

function listHtml(items, emptyText = 'موردی ثبت نشده است.') {
  if (!items?.length) return `<p class="structured-empty">${escapeHtml(emptyText)}</p>`;
  return `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`;
}

function confidenceHtml(value) {
  const numeric = Number(value ?? 0);
  const percent = Math.round(Math.max(0, Math.min(1, numeric)) * 100);
  return `<span class="confidence"><span style="width:${percent}%"></span></span><strong>${percent}٪</strong>`;
}

function evidenceReferencesHtml(references) {
  if (!references?.length) return '<span class="muted-text">بدون ارجاع</span>';
  return `<div class="reference-list">${references.map((ref) => `
    <div class="reference-chip">
      <strong>منبع ${escapeHtml(ref.source_number)}</strong>
      <span>${escapeHtml(ref.filename)} · ${ref.chunk_index == null ? 'کارت مثال' : `قطعه ${escapeHtml(ref.chunk_index)}`}</span>
      <small>${escapeHtml(ref.support)}</small>
    </div>`).join('')}</div>`;
}

function renderProfessorProfile(profile) {
  const statusLabels = {supported: 'مستند', inferred: 'استنباط', unknown: 'نامعلوم'};
  const claimCards = (profile.claims || []).map((claim) => `
    <article class="structured-card claim-${escapeHtml(claim.status)}">
      <div class="structured-card-head">
        <div><span class="pill">${escapeHtml(claim.category)}</span><strong>${escapeHtml(statusLabels[claim.status] || claim.status)}</strong></div>
        <div class="confidence-row">${confidenceHtml(claim.confidence)}</div>
      </div>
      <p>${escapeHtml(claim.claim)}</p>
      ${evidenceReferencesHtml(claim.evidence_refs)}
    </article>`).join('');

  return `
    <section class="structured-output profile-output">
      <div class="structured-summary">
        <div><span>درس</span><strong>${escapeHtml(profile.course_name)}</strong></div>
        <div><span>استاد</span><strong>${escapeHtml(profile.professor_name)}</strong></div>
        <div><span>شواهد ارجاع‌شده</span><strong>${escapeHtml(profile.evidence_count)}</strong></div>
        <div><span>اطمینان کلی</span><div class="confidence-row">${confidenceHtml(profile.overall_confidence)}</div></div>
      </div>
      <div class="structured-section"><h3>ادعاهای پروفایل</h3><div class="structured-card-list">${claimCards || '<p class="structured-empty">ادعایی ساخته نشده است.</p>'}</div></div>
      <div class="structured-columns">
        <div class="structured-section"><h3>راهبرد پیشنهادی امتحان</h3>${listHtml(profile.recommended_exam_strategy)}</div>
        <div class="structured-section"><h3>موارد نامعلوم</h3>${listHtml(profile.unknowns)}</div>
      </div>
      <div class="structured-section"><h3>محدودیت‌ها</h3>${listHtml(profile.limitations)}</div>
    </section>`;
}

function renderErrorGroup(title, items, className = '') {
  if (!items?.length) return '';
  return `<div class="error-group ${className}"><h4>${escapeHtml(title)}</h4>${listHtml(items)}</div>`;
}

function renderGradingReport(report) {
  const rows = (report.score_breakdown || []).map((item) => `
    <tr>
      <td><strong>${escapeHtml(item.criterion)}</strong><small>${escapeHtml(item.rationale)}</small></td>
      <td>${escapeHtml(item.max_score)}</td>
      <td>${escapeHtml(item.awarded_score)}</td>
    </tr>`).join('');

  const missing = (report.missing_steps || []).map((item) => `
    <article class="missing-step severity-${escapeHtml(item.severity)}">
      <div><span class="pill">${escapeHtml(item.severity)}</span><strong>${escapeHtml(item.step)}</strong></div>
      <p>${escapeHtml(item.impact)}</p>
      <small>اصلاح: ${escapeHtml(item.suggested_fix)}</small>
    </article>`).join('');

  const professorRange = report.likely_professor_score
    ? `<div class="score-range"><span>بازه احتمالی نزد استاد</span><strong>${escapeHtml(report.likely_professor_score.minimum)} تا ${escapeHtml(report.likely_professor_score.maximum)} از ${escapeHtml(report.likely_professor_score.scale_max)}</strong></div>`
    : '';

  const saveButton = report.suggested_mistake
    ? '<button type="button" class="button primary" id="save-suggested-mistake">ذخیره پیشنهاد در دفترچه خطا</button>'
    : '';

  return `
    <section class="structured-output grading-output">
      <div class="grading-hero">
        <div class="score-circle"><strong>${escapeHtml(report.total_score)}</strong><span>از ${escapeHtml(report.max_score)}</span></div>
        <div><span class="eyebrow">GRADING REPORT</span><h3>تصحیح ساختاریافته</h3><div class="confidence-row">${confidenceHtml(report.confidence)}</div></div>
        ${professorRange}
      </div>
      <div class="structured-section">
        <h3>تقسیم نمره</h3>
        <div class="table-wrap"><table class="score-table"><thead><tr><th>معیار</th><th>بارم</th><th>نمره</th></tr></thead><tbody>${rows}</tbody><tfoot><tr><th>مجموع</th><th>${escapeHtml(report.max_score)}</th><th>${escapeHtml(report.total_score)}</th></tr></tfoot></table></div>
      </div>
      ${report.first_divergence ? `<div class="first-divergence"><strong>اولین نقطه انحراف</strong><p>${escapeHtml(report.first_divergence)}</p></div>` : ''}
      ${missing ? `<div class="structured-section"><h3>مراحل حذف‌شده</h3><div class="missing-list">${missing}</div></div>` : ''}
      <div class="error-grid">
        ${renderErrorGroup('خطاهای علمی', report.scientific_errors, 'danger')}
        ${renderErrorGroup('خطاهای محاسباتی', report.calculation_errors, 'warning')}
        ${renderErrorGroup('خطاهای نمادگذاری', report.notation_errors)}
        ${renderErrorGroup('نقاط قوت', report.strengths, 'success')}
      </div>
      ${report.corrected_answer ? `<div class="structured-section"><h3>پاسخ اصلاح‌شده</h3><pre class="corrected-answer">${escapeHtml(report.corrected_answer)}</pre></div>` : ''}
      ${report.suggested_mistake ? `<div class="mistake-suggestion"><div><span class="pill">${escapeHtml(report.suggested_mistake.category || 'پیشنهاد خطا')}</span><strong>${escapeHtml(report.suggested_mistake.topic || 'خطای پیشنهادی')}</strong><p>${escapeHtml(report.suggested_mistake.description)}</p><small>${escapeHtml(report.suggested_mistake.prevention)}</small></div>${saveButton}</div>` : ''}
    </section>`;
}

function renderStudyPlan(plan) {
  const priorities = (plan.priorities || []).map((item) => `
    <article class="priority-card priority-${escapeHtml(item.priority)}">
      <div><span class="pill">${escapeHtml(item.priority)}</span><strong>${escapeHtml(item.topic)}</strong></div>
      <p>${escapeHtml(item.reason)}</p>
      ${evidenceReferencesHtml(item.evidence_refs)}
    </article>`).join('');

  const days = (plan.days || []).map((day) => `
    <article class="study-day">
      <div class="study-day-head"><div><span>روز ${escapeHtml(day.day_number)}</span><strong>${escapeHtml(day.focus)}</strong></div><small>${escapeHtml(day.calendar_date || '')} · ${escapeHtml(day.total_minutes)} دقیقه</small></div>
      <div class="task-list">${(day.tasks || []).map((task) => `
        <div class="study-task">
          <div><span class="pill">${escapeHtml(task.task_type)}</span><strong>${escapeHtml(task.title)}</strong></div>
          <small>${escapeHtml(task.estimated_minutes)} دقیقه${task.exercise_count != null ? ` · ${escapeHtml(task.exercise_count)} تمرین` : ''}</small>
          <p>معیار پایان: ${escapeHtml(task.completion_criteria)}</p>
        </div>`).join('')}</div>
      ${day.short_test ? `<div class="short-test"><strong>آزمون کوتاه</strong><p>${escapeHtml(day.short_test)}</p></div>` : ''}
    </article>`).join('');

  return `
    <section class="structured-output plan-output">
      <div class="structured-summary">
        <div><span>درس</span><strong>${escapeHtml(plan.course_name)}</strong></div>
        <div><span>مدت</span><strong>${escapeHtml(plan.duration_days)} روز</strong></div>
        <div><span>زمان روزانه</span><strong>${escapeHtml(plan.daily_minutes)} دقیقه</strong></div>
        <div><span>اطمینان</span><div class="confidence-row">${confidenceHtml(plan.confidence)}</div></div>
      </div>
      <div class="structured-section"><h3>اولویت‌ها</h3><div class="priority-list">${priorities || '<p class="structured-empty">اولویتی ثبت نشده است.</p>'}</div></div>
      <div class="structured-section"><h3>برنامه روزانه</h3><div class="study-days">${days}</div></div>
      <div class="structured-columns">
        <div class="structured-section"><h3>فرض‌های برنامه</h3>${listHtml(plan.assumptions)}</div>
        <div class="structured-section"><h3>کنترل ریسک</h3>${listHtml(plan.risk_controls)}</div>
      </div>
      <div class="structured-section"><h3>مرور نهایی</h3>${listHtml(plan.final_review)}</div>
    </section>`;
}

function renderStructuredOutput(schema, payload) {
  if (schema === 'ProfessorProfile') return renderProfessorProfile(payload);
  if (schema === 'GradingReport') return renderGradingReport(payload);
  if (schema === 'StudyPlan') return renderStudyPlan(payload);
  return `<pre class="corrected-answer">${escapeHtml(JSON.stringify(payload, null, 2))}</pre>`;
}

function reliabilityHtml(data) {
  if (data.validation_status === 'invalid_fallback') {
    return `<div class="reliability-banner invalid">
      <strong>این خروجی ساختاریافته معتبر نیست</strong>
      <p>پاسخ مدل پس از یک تلاش اصلاحی هم schema یا ارجاعات evidence را پاس نکرد. این متن را مبنای نمره، پروفایل استاد یا برنامه قطعی قرار نده.</p>
      <details><summary>جزئیات خطا</summary><pre>${escapeHtml(data.validation_error || 'خطای نامشخص')}</pre></details>
    </div>`;
  }
  if (data.validation_status === 'recovered') {
    return `<div class="reliability-banner recovered"><strong>خروجی پس از یک retry اصلاح شد</strong><p>پاسخ اول نامعتبر بود؛ پاسخ دوم قرارداد schema و ارجاعات evidence را پاس کرده است.</p></div>`;
  }
  if (data.validation_status === 'valid' && data.schema) {
    return '<div class="reliability-banner valid"><strong>خروجی ساختاریافته معتبر</strong><p>Schema و ارجاعات evidence این run بررسی شده‌اند.</p></div>';
  }
  return '';
}

function evidenceHtml(items) {
  return items?.length
    ? `<details class="evidence"><summary>${items.length} شاهد استفاده شد</summary>${items.map((item, index) => `<div><strong>منبع ${index + 1}: ${escapeHtml(item.filename)}</strong><small>${item.evidence_kind === 'example_card' ? 'کارت مثال تأییدشده' : `قطعه ${escapeHtml(item.chunk_index)}`} · امتیاز ${escapeHtml(item.score ?? 0)}</small></div>`).join('')}</details>`
    : '<div class="notice">منبع مرتبطی بازیابی نشد؛ خروجی با عدم‌قطعیت بیشتری تولید شده است.</div>';
}

async function saveSuggestedMistake(courseId, suggestion, button) {
  if (!window.confirm('این پیشنهاد پس از تأیید تو در دفترچه خطا ذخیره شود؟')) return;
  button.disabled = true;
  button.textContent = 'در حال ذخیره…';
  try {
    const response = await fetch(`/api/courses/${courseId}/mistakes`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(suggestion),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'ثبت خطا ناموفق بود');
    button.textContent = 'در دفترچه ذخیره شد';
    button.classList.remove('primary');
    button.classList.add('ghost');
    toast('خطا با تأیید تو ذخیره شد', 'success');
  } catch (error) {
    button.disabled = false;
    button.textContent = 'ذخیره پیشنهاد در دفترچه خطا';
    toast(error.message, 'error');
  }
}

const coachForm = $('#coach-form');
if (coachForm) {
  coachForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const prompt = $('#coach-prompt').value.trim();
    if (!prompt) return;
    const courseId = coachForm.dataset.courseId;
    const output = $('#coach-output');
    const button = $('#run-button');
    button.disabled = true;
    button.textContent = 'در حال اجرا…';
    output.classList.remove('empty-output');
    output.innerHTML = '<div class="loading"><span></span><span></span><span></span></div>';
    try {
      const response = await fetch(`/api/courses/${courseId}/run`, {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({mode: currentMode, prompt})
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'خطا در اجرا');

      const mainOutput = data.structured_output
        ? renderStructuredOutput(data.schema, data.structured_output)
        : `<div class="generated-output raw-fallback">${simpleMarkdown(data.output)}</div>`;

      output.innerHTML = `${reliabilityHtml(data)}${mainOutput}${evidenceHtml(data.evidence)}<div class="provider-tag">${escapeHtml(data.provider)}${data.retry_count ? ` · retry ${escapeHtml(data.retry_count)}` : ''}</div>`;

      const saveButton = $('#save-suggested-mistake', output);
      if (saveButton && data.structured_output?.suggested_mistake) {
        saveButton.addEventListener('click', () => saveSuggestedMistake(courseId, data.structured_output.suggested_mistake, saveButton));
      }

      if (data.validation_status === 'invalid_fallback') {
        toast('خروجی معتبر نشد؛ هشدار را بررسی کن', 'error');
      } else if (data.validation_status === 'recovered') {
        toast('خروجی با یک retry اصلاح و ذخیره شد', 'success');
      } else {
        toast('خروجی ذخیره شد', 'success');
      }
    } catch (error) {
      output.innerHTML = `<div class="error-box">${escapeHtml(error.message)}</div>`;
      toast(error.message, 'error');
    } finally {
      button.disabled = false;
      button.textContent = 'اجرا';
    }
  });
}

"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { Icons } from "@/components/icons";
import { api } from "@/lib/api";
import type { ModelCatalogItem, ModelConnection, ModelConnectionInput } from "@/lib/types";

const defaults: Record<ModelConnection["protocol"], string> = {
  gemini: "https://generativelanguage.googleapis.com/v1beta",
  openai_compatible: "https://api.openai.com/v1",
};

function emptyConnection(slot: 1 | 2): ModelConnection {
  const protocol = slot === 1 ? "gemini" : "openai_compatible";
  return {
    slot,
    label: `اتصال ${slot}`,
    protocol,
    base_url: defaults[protocol],
    selected_model: "",
    active: false,
    has_api_key: false,
    cached_models: [],
    cache_updated_at: null,
  };
}

function compactNumber(value: number | null) {
  if (!value) return "";
  return new Intl.NumberFormat("fa-IR", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

function ModelPicker({
  models,
  selected,
  onSelect,
}: {
  models: ModelCatalogItem[];
  selected: string;
  onSelect: (value: string) => void;
}) {
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const matches = needle
      ? models.filter((model) => `${model.name} ${model.id} ${model.description}`.toLowerCase().includes(needle))
      : models;
    return matches.slice(0, 8);
  }, [models, query]);

  return (
    <div className="model-picker">
      <div className="model-picker-head">
        <label className="field model-search">
          <span>مدل</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={models.length ? `جست‌وجو بین ${models.length} مدل` : "اول مدل‌ها را دریافت کن"}
          />
        </label>
        {selected && <span className="selected-model-chip">{selected}</span>}
      </div>
      {models.length > 0 && (
        <div className="model-results">
          {filtered.length ? filtered.map((model) => (
            <button
              type="button"
              className={selected === model.id ? "model-option selected" : "model-option"}
              key={model.id}
              onClick={() => onSelect(model.id)}
            >
              <div>
                <strong>{model.name}</strong>
                <small>{model.id}</small>
              </div>
              <div className="model-meta">
                {model.free === true && <span className="free-pill">رایگان</span>}
                {model.thinking === true && <span>Thinking</span>}
                {model.context_length ? <span>{compactNumber(model.context_length)} توکن</span> : null}
              </div>
            </button>
          )) : <div className="model-empty">مدلی با این عبارت پیدا نشد.</div>}
        </div>
      )}
    </div>
  );
}

function ConnectionCard({
  initial,
  onChanged,
}: {
  initial: ModelConnection;
  onChanged: () => Promise<void>;
}) {
  const [form, setForm] = useState<ModelConnectionInput>({
    label: initial.label,
    protocol: initial.protocol,
    base_url: initial.base_url,
    api_key: "",
    selected_model: initial.selected_model,
    active: initial.active,
  });
  const [models, setModels] = useState(initial.cached_models);
  const [busy, setBusy] = useState<"save" | "discover" | "test" | "delete" | "">("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    setForm({
      label: initial.label,
      protocol: initial.protocol,
      base_url: initial.base_url,
      api_key: "",
      selected_model: initial.selected_model,
      active: initial.active,
    });
    setModels(initial.cached_models);
  }, [initial]);

  function changeProtocol(protocol: ModelConnection["protocol"]) {
    setForm((current) => ({
      ...current,
      protocol,
      base_url: defaults[protocol],
      selected_model: "",
    }));
    setModels([]);
  }

  async function save(event?: FormEvent) {
    event?.preventDefault();
    setBusy("save"); setError(""); setMessage("");
    try {
      await api.saveModelConnection(initial.slot, {
        ...form,
        api_key: form.api_key?.trim() || null,
      });
      setForm((current) => ({ ...current, api_key: "" }));
      setMessage("تنظیمات ذخیره شد.");
      await onChanged();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "ذخیره اتصال ناموفق بود.");
    } finally {
      setBusy("");
    }
  }

  async function discover() {
    setBusy("discover"); setError(""); setMessage("");
    try {
      await api.saveModelConnection(initial.slot, { ...form, api_key: form.api_key?.trim() || null });
      const items = await api.discoverModels(initial.slot);
      setModels(items);
      setForm((current) => ({ ...current, api_key: "" }));
      setMessage(`${items.length} مدل قابل استفاده پیدا شد.`);
      await onChanged();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "دریافت مدل‌ها ناموفق بود.");
    } finally {
      setBusy("");
    }
  }

  async function test() {
    setBusy("test"); setError(""); setMessage("");
    try {
      await api.saveModelConnection(initial.slot, { ...form, api_key: form.api_key?.trim() || null });
      const result = await api.testModelConnection(initial.slot);
      setForm((current) => ({ ...current, api_key: "" }));
      setMessage(result.ok ? `اتصال سالم است: ${result.provider}` : "مدل پاسخ معتبری نداد.");
      await onChanged();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "تست اتصال ناموفق بود.");
    } finally {
      setBusy("");
    }
  }

  async function remove() {
    if (!window.confirm("این اتصال و کلید محلی آن حذف شود؟")) return;
    setBusy("delete"); setError("");
    try {
      await api.deleteModelConnection(initial.slot);
      setMessage("اتصال حذف شد.");
      await onChanged();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "حذف اتصال ناموفق بود.");
    } finally {
      setBusy("");
    }
  }

  return (
    <form className={form.active ? "connection-card active" : "connection-card"} onSubmit={save}>
      <div className="connection-card-head">
        <div>
          <span className="eyebrow">API SLOT {initial.slot}</span>
          <input
            className="connection-title-input"
            value={form.label}
            onChange={(event) => setForm({ ...form, label: event.target.value })}
          />
        </div>
        <label className="active-toggle">
          <input
            type="checkbox"
            checked={form.active}
            onChange={(event) => setForm({ ...form, active: event.target.checked })}
          />
          <span>{form.active ? "فعال" : "غیرفعال"}</span>
        </label>
      </div>

      <div className="connection-form-grid">
        <label className="field">
          <span>نوع API</span>
          <select value={form.protocol} onChange={(event) => changeProtocol(event.target.value as ModelConnection["protocol"])}>
            <option value="gemini">Gemini API</option>
            <option value="openai_compatible">OpenAI-compatible</option>
          </select>
        </label>
        <label className="field">
          <span>Base URL</span>
          <input dir="ltr" value={form.base_url} onChange={(event) => setForm({ ...form, base_url: event.target.value })} />
        </label>
      </div>

      <label className="field">
        <span>API Key {initial.has_api_key && <small>کلید قبلی محفوظ است</small>}</span>
        <input
          dir="ltr"
          type="password"
          autoComplete="off"
          value={form.api_key ?? ""}
          onChange={(event) => setForm({ ...form, api_key: event.target.value })}
          placeholder={initial.has_api_key ? "برای حفظ کلید فعلی خالی بگذار" : "کلید API را وارد کن"}
        />
      </label>

      <ModelPicker models={models} selected={form.selected_model} onSelect={(model) => setForm({ ...form, selected_model: model })} />

      {error && <div className="inline-status error"><Icons.Alert />{error}</div>}
      {message && <div className="inline-status success"><Icons.Check />{message}</div>}

      <div className="connection-actions">
        <button className="button primary" disabled={Boolean(busy)}>{busy === "save" ? "در حال ذخیره…" : "ذخیره"}</button>
        <button type="button" className="button secondary" onClick={() => void discover()} disabled={Boolean(busy)}>
          <Icons.Refresh /> {busy === "discover" ? "در حال دریافت…" : "دریافت مدل‌ها"}
        </button>
        <button type="button" className="button secondary" onClick={() => void test()} disabled={Boolean(busy) || !form.selected_model}>
          {busy === "test" ? "در حال تست…" : "تست مدل"}
        </button>
        <button type="button" className="icon-button danger" title="حذف اتصال" onClick={() => void remove()} disabled={Boolean(busy)}><Icons.Trash /></button>
      </div>
    </form>
  );
}

export function ModelSettings() {
  const [connections, setConnections] = useState<ModelConnection[]>([]);
  const [activeProvider, setActiveProvider] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const data = await api.listModelConnections();
      setConnections(data.items);
      setActiveProvider(data.active_provider);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "تنظیمات مدل بارگذاری نشد.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, []);

  if (loading) return <div className="model-settings-loading">در حال بارگذاری تنظیمات مدل…</div>;

  return (
    <section className="model-settings-shell">
      <div className="model-settings-hero">
        <div>
          <span className="eyebrow">MODEL RUNTIME</span>
          <h1>اتصال مدل</h1>
          <p>حداکثر دو API نگه دار. مدل‌ها مستقیم از همان سرویس دریافت می‌شوند و هیچ فهرستی در برنامه هاردکد نشده است.</p>
        </div>
        <div className={activeProvider ? "runtime-status online" : "runtime-status"}>
          <span />
          <div><small>مدل فعال</small><strong>{activeProvider || "هنوز انتخاب نشده"}</strong></div>
        </div>
      </div>
      {error && <div className="alert error"><Icons.Alert />{error}</div>}
      <div className="connection-grid">
        {(connections.length ? connections : [emptyConnection(1), emptyConnection(2)]).map((connection) => (
          <ConnectionCard key={connection.slot} initial={connection} onChanged={load} />
        ))}
      </div>
      <div className="privacy-note">
        <Icons.Alert />
        <p>کلیدها فقط روی همین سیستم در <code>data/model_secrets.json</code> ذخیره می‌شوند، از API به مرورگر برگردانده نمی‌شوند و داخل Git قرار نمی‌گیرند.</p>
      </div>
    </section>
  );
}

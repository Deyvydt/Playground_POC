import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Check, Copy, KeyRound, Landmark, Loader2, Pause, Pencil, Play, Plus, RefreshCw, ServerOff, Trash2, TriangleAlert,
} from "lucide-react";
import PageHeader from "../components/PageHeader";
import Modal from "../components/Modal";
import Badge from "../components/Badge";
import Tooltip from "../components/Tooltip";
import EmptyState from "../components/EmptyState";
import { useSession } from "../context/SessionContext";
import { useUI } from "../context/UIContext";
import {
  errorMessage, govAgent, govAgentActivity, govAgents, govAreas, govCreateSistema, govDeleteAgent, govPauseAgent,
  govRegenerateKey, govRegisterAgent, govResumeAgent, govSistemas, govUpdateAgent,
} from "../api/client";
import { fmtLatency, fmtNumber, fmtRelative, fmtUSD } from "../lib/format";

const PERIODS = [
  { id: "1d", label: "Diario" },
  { id: "7d", label: "Semanal" },
  { id: "30d", label: "Mensual" },
];
const MODEL_GROUPS = [
  { id: "local-models", label: "Modelos locales" },
  { id: "cloud-models", label: "Modelos en la nube" },
];

const ratioTone = (r) => (r == null ? "bg-mist-300" : r >= 1 ? "bg-red-500" : r >= 0.8 ? "bg-amber-500" : "bg-ink-950/70");

function BudgetBar({ usage, compact = false }) {
  if (!usage?.available) return <span className="text-[12px] text-mist-400">Sin datos del gateway</span>;
  const ratio = usage.budget_ratio;
  return (
    <div className={compact ? "w-40" : ""}>
      <div className="flex items-baseline justify-between gap-2 text-[12px]">
        <span className="font-medium tabular text-ink-950">{fmtUSD(usage.spend)}</span>
        <span className="tabular text-mist-500">{usage.max_budget != null ? `de ${fmtUSD(usage.max_budget)}` : "sin tope"}</span>
      </div>
      <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-mist-100">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, (ratio || 0) * 100)}%` }}
          transition={{ duration: 0.7 }}
          className={`h-full rounded-full ${ratioTone(ratio)}`}
        />
      </div>
    </div>
  );
}

function CopyButton({ text, label = "Copiar" }) {
  const [done, setDone] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setDone(true);
      setTimeout(() => setDone(false), 1500);
    } catch {
      /* el navegador no permite el portapapeles */
    }
  };
  return (
    <button type="button" onClick={copy} className="btn-secondary px-2.5 py-1.5 text-[12px]">
      {done ? <Check size={13} /> : <Copy size={13} />} {done ? "Copiado" : label}
    </button>
  );
}

function KeyRevealModal({ result, onClose }) {
  const [tab, setTab] = useState("python");
  const conn = result?.connection;
  return (
    <Modal open={Boolean(result)} onClose={onClose} size="lg" title="Key del agente" subtitle={result?.agent?.name}>
      {conn && (
        <div className="space-y-5 px-6 py-5">
          <div className="flex gap-2.5 rounded-lg border border-amber-200 bg-amber-50 p-3 text-[12.5px] text-amber-800">
            <TriangleAlert size={16} className="mt-0.5 shrink-0" />
            Esta es la única vez que se muestra la key. Cópiala y entrégala al encargado del agente; si se pierde, hay que regenerarla.
          </div>
          <div>
            <span className="label">Virtual key</span>
            <div className="flex items-center gap-2">
              <code className="min-w-0 flex-1 truncate rounded-lg border border-mist-200 bg-mist-50 px-3 py-2 font-mono text-[12.5px] text-ink-950">
                {conn.api_key}
              </code>
              <CopyButton text={conn.api_key} />
            </div>
          </div>
          <div>
            <span className="label">URL base</span>
            <div className="flex items-center gap-2">
              <code className="min-w-0 flex-1 truncate rounded-lg border border-mist-200 bg-mist-50 px-3 py-2 font-mono text-[12.5px] text-ink-950">
                {conn.base_url}
              </code>
              <CopyButton text={conn.base_url} />
            </div>
          </div>
          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="label mb-0">Guía de conexión</span>
              <div className="flex items-center gap-2">
                <CopyButton text={conn[tab].replaceAll("<VIRTUAL_KEY>", conn.api_key).replaceAll("${VIRTUAL_KEY}", conn.api_key)} label="Copiar con key" />
                <div className="inline-flex rounded-lg border border-mist-200 bg-white p-0.5">
                  {[["python", "Python"], ["java", "Java"], ["curl", "cURL"]].map(([id, label]) => (
                    <button
                      key={id}
                      onClick={() => setTab(id)}
                      className={`focus-ring rounded-md px-3 py-1 text-[12px] font-medium transition ${tab === id ? "bg-ink-950 text-white" : "text-mist-500 hover:text-ink-950"}`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <pre className="overflow-x-auto rounded-lg bg-ink-950 p-4 font-mono text-[12px] leading-relaxed text-white/90">{conn[tab]}</pre>
            <p className="mt-2 text-[12px] text-mist-500">
              Modelos habilitados: {conn.models.join(", ")}. Usa el alias <code className="font-mono">{conn.example_model}</code> como nombre de modelo.
            </p>
          </div>
        </div>
      )}
      <div className="flex justify-end border-t border-mist-100 px-6 py-4">
        <button onClick={onClose} className="btn-primary">Listo, ya la copié</button>
      </div>
    </Modal>
  );
}

const EMPTY_AGENT = {
  name: "", sistema_id: "", description: "", owner_name: "", owner_email: "", models: ["local-models"],
  max_budget: 1, budget_duration: "30d", rpm_limit: "", tpm_limit: "",
};

const numOrNull = (v) => (v === "" || v == null ? null : Number(v));

function LimitsFields({ form, set, toggleModel }) {
  return (
    <>
      <div>
        <span className="label">Modelos permitidos</span>
        <div className="flex flex-wrap gap-2">
          {MODEL_GROUPS.map((g) => {
            const on = form.models.includes(g.id);
            return (
              <button
                type="button"
                key={g.id}
                onClick={() => toggleModel(g.id)}
                className={`focus-ring inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[12.5px] font-medium transition ${
                  on ? "border-ink-950 bg-ink-950 text-white" : "border-mist-200 bg-white text-ink-700 hover:border-mist-300"
                }`}
              >
                {on && <Check size={13} />} {g.label}
              </button>
            );
          })}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="label" htmlFor="lim-budget">Presupuesto (USD)</label>
          <input id="lim-budget" type="number" min="0" step="0.01" className="input" value={form.max_budget ?? ""} onChange={set("max_budget")} placeholder="Sin tope" />
        </div>
        <div>
          <label className="label" htmlFor="lim-period">Periodo</label>
          <select id="lim-period" className="input" value={form.budget_duration || "30d"} onChange={set("budget_duration")}>
            {PERIODS.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="lim-rpm">Solicitudes por minuto</label>
          <input id="lim-rpm" type="number" min="1" className="input" value={form.rpm_limit ?? ""} onChange={set("rpm_limit")} placeholder="Sin límite" />
        </div>
        <div>
          <label className="label" htmlFor="lim-tpm">Tokens por minuto</label>
          <input id="lim-tpm" type="number" min="1" className="input" value={form.tpm_limit ?? ""} onChange={set("tpm_limit")} placeholder="Sin límite" />
        </div>
      </div>
    </>
  );
}

function useForm(initial) {
  const [form, setForm] = useState(initial);
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));
  const toggleModel = (id) =>
    setForm((f) => {
      const models = f.models.includes(id) ? f.models.filter((m) => m !== id) : [...f.models, id];
      return { ...f, models: models.length ? models : f.models };
    });
  return { form, setForm, set, toggleModel };
}

function RegisterAgentModal({ open, sistemas, onClose, onDone }) {
  const { form, setForm, set, toggleModel } = useForm(EMPTY_AGENT);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (open) {
      setForm({ ...EMPTY_AGENT, sistema_id: sistemas[0]?.id ?? "" });
      setError("");
    }
  }, [open, sistemas, setForm]);

  const sistema = sistemas.find((s) => s.id === Number(form.sistema_id));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const result = await govRegisterAgent({
        ...form,
        sistema_id: Number(form.sistema_id),
        max_budget: numOrNull(form.max_budget),
        rpm_limit: numOrNull(form.rpm_limit),
        tpm_limit: numOrNull(form.tpm_limit),
      });
      onDone(result);
    } catch (err) {
      setError(errorMessage(err, "No se pudo registrar el agente"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} size="lg" title="Registrar agente" subtitle="Se emite una virtual key con sus propios límites de gasto y uso">
      <form onSubmit={submit} className="space-y-4 px-6 py-5">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label" htmlFor="ag-name">Nombre</label>
            <input id="ag-name" className="input" required minLength={2} value={form.name} onChange={set("name")} placeholder="Ej. Clasificador de tickets" />
          </div>
          <div>
            <label className="label" htmlFor="ag-sistema">Sistema</label>
            <select id="ag-sistema" className="input" required value={form.sistema_id} onChange={set("sistema_id")}>
              {sistemas.map((s) => <option key={s.id} value={s.id}>{s.name} · {s.area_name}</option>)}
            </select>
          </div>
          <div>
            <label className="label" htmlFor="ag-owner">Encargado</label>
            <input id="ag-owner" className="input" value={form.owner_name} onChange={set("owner_name")} placeholder="Nombre y apellido" />
          </div>
          <div>
            <label className="label" htmlFor="ag-email">Correo del encargado</label>
            <input id="ag-email" type="email" className="input" value={form.owner_email} onChange={set("owner_email")} placeholder="nombre@tcs.com" />
          </div>
        </div>
        <div>
          <label className="label" htmlFor="ag-desc">Descripción</label>
          <input id="ag-desc" className="input" value={form.description} onChange={set("description")} placeholder="Qué hace y quién lo usa" />
        </div>
        <LimitsFields form={form} set={set} toggleModel={toggleModel} />
        {sistema && <p className="text-[12px] text-mist-500">El gasto se sumará al presupuesto del área {sistema.area_name}.</p>}
        {error && <p className="text-[12.5px] text-red-600">{error}</p>}
        <div className="flex justify-end gap-2 pt-1">
          <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
          <button type="submit" disabled={saving || !form.name.trim() || !form.sistema_id} className="btn-primary">
            {saving ? <Loader2 size={14} className="animate-spin" /> : <KeyRound size={14} />} Registrar y emitir key
          </button>
        </div>
      </form>
    </Modal>
  );
}

function LimitsModal({ agent, onClose, onDone }) {
  const { form, setForm, set, toggleModel } = useForm(EMPTY_AGENT);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!agent) return;
    setForm({
      ...EMPTY_AGENT,
      models: agent.models,
      max_budget: agent.max_budget ?? "",
      budget_duration: agent.budget_duration || "30d",
      rpm_limit: agent.rpm_limit ?? "",
      tpm_limit: agent.tpm_limit ?? "",
      owner_name: agent.owner_name,
      owner_email: agent.owner_email,
    });
    setError("");
  }, [agent, setForm]);

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await govUpdateAgent(agent.id, {
        models: form.models,
        max_budget: numOrNull(form.max_budget),
        budget_duration: form.budget_duration,
        rpm_limit: numOrNull(form.rpm_limit),
        tpm_limit: numOrNull(form.tpm_limit),
        owner_name: form.owner_name,
        owner_email: form.owner_email,
      });
      onDone();
    } catch (err) {
      setError(errorMessage(err, "No se pudieron guardar los límites"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open={Boolean(agent)} onClose={onClose} title="Editar límites" subtitle={agent?.name}>
      <form onSubmit={submit} className="space-y-4 px-6 py-5">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label" htmlFor="lim-owner">Encargado</label>
            <input id="lim-owner" className="input" value={form.owner_name} onChange={set("owner_name")} />
          </div>
          <div>
            <label className="label" htmlFor="lim-email">Correo</label>
            <input id="lim-email" type="email" className="input" value={form.owner_email} onChange={set("owner_email")} />
          </div>
        </div>
        <LimitsFields form={form} set={set} toggleModel={toggleModel} />
        {error && <p className="text-[12.5px] text-red-600">{error}</p>}
        <div className="flex justify-end gap-2 pt-1">
          <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
          <button type="submit" disabled={saving} className="btn-primary">
            {saving && <Loader2 size={14} className="animate-spin" />} Guardar
          </button>
        </div>
      </form>
    </Modal>
  );
}

function PauseModal({ agent, onClose, onDone }) {
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setReason("");
    setError("");
  }, [agent]);

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await govPauseAgent(agent.id, reason.trim());
      onDone();
    } catch (err) {
      setError(errorMessage(err, "No se pudo pausar el agente"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open={Boolean(agent)} onClose={onClose} size="sm" title="Pausar agente" subtitle={agent?.name}>
      <form onSubmit={submit} className="space-y-4 px-6 py-5">
        <p className="text-[13px] text-ink-700">El gateway rechazará sus llamadas de inmediato hasta que lo reactives.</p>
        <div>
          <label className="label" htmlFor="pause-reason">Motivo</label>
          <textarea id="pause-reason" required rows={3} maxLength={300} className="input resize-none" value={reason}
            onChange={(e) => setReason(e.target.value)} placeholder="Ej. Consumo anómalo en revisión" />
        </div>
        {error && <p className="text-[12.5px] text-red-600">{error}</p>}
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
          <button type="submit" disabled={saving || !reason.trim()} className="btn-accent">
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Pause size={14} />} Pausar
          </button>
        </div>
      </form>
    </Modal>
  );
}

function SistemaModal({ open, areas, onClose, onDone }) {
  const [form, setForm] = useState({ name: "", area_id: "", description: "", owner_name: "", owner_email: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (open) {
      setForm({ name: "", area_id: areas[0]?.id ?? "", description: "", owner_name: "", owner_email: "" });
      setError("");
    }
  }, [open, areas]);
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));
  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await govCreateSistema(form);
      onDone();
    } catch (err) {
      setError(errorMessage(err, "No se pudo crear el sistema"));
    } finally {
      setSaving(false);
    }
  };
  return (
    <Modal open={open} onClose={onClose} title="Nuevo sistema" subtitle="Agrupa los agentes de una misma aplicación dentro de un área">
      <form onSubmit={submit} className="space-y-4 px-6 py-5">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label" htmlFor="sis-name">Nombre</label>
            <input id="sis-name" className="input" required minLength={2} value={form.name} onChange={set("name")} />
          </div>
          <div>
            <label className="label" htmlFor="sis-area">Área</label>
            <select id="sis-area" className="input" value={form.area_id} onChange={set("area_id")}>
              {areas.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </div>
          <div>
            <label className="label" htmlFor="sis-owner">Encargado</label>
            <input id="sis-owner" className="input" value={form.owner_name} onChange={set("owner_name")} />
          </div>
          <div>
            <label className="label" htmlFor="sis-email">Correo</label>
            <input id="sis-email" type="email" className="input" value={form.owner_email} onChange={set("owner_email")} />
          </div>
        </div>
        <div>
          <label className="label" htmlFor="sis-desc">Descripción</label>
          <input id="sis-desc" className="input" value={form.description} onChange={set("description")} />
        </div>
        {error && <p className="text-[12.5px] text-red-600">{error}</p>}
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
          <button type="submit" disabled={saving || !form.name.trim()} className="btn-primary">
            {saving && <Loader2 size={14} className="animate-spin" />} Crear sistema
          </button>
        </div>
      </form>
    </Modal>
  );
}

const STATUS_LABEL = { success: "Correcta", failure: "Error" };

function AgentDetailModal({ agentId, onClose }) {
  const [agent, setAgent] = useState(null);
  const [activity, setActivity] = useState(null);
  const [activityError, setActivityError] = useState("");

  useEffect(() => {
    if (!agentId) return;
    setAgent(null);
    setActivity(null);
    setActivityError("");
    govAgent(agentId).then(setAgent).catch(() => {});
    govAgentActivity(agentId)
      .then(setActivity)
      .catch((err) => setActivityError(errorMessage(err, "No se pudo leer la actividad")));
  }, [agentId]);

  return (
    <Modal open={Boolean(agentId)} onClose={onClose} size="lg" title={agent?.name || "Agente"} subtitle={agent && `${agent.sistema.name} · ${agent.area.name}`}>
      {!agent ? (
        <div className="grid place-items-center py-16 text-mist-400"><Loader2 className="animate-spin" size={18} /></div>
      ) : (
        <div className="space-y-5 px-6 py-5">
          {agent.status === "pausado" && (
            <div className="rounded-lg border border-red-100 bg-red-50 p-3 text-[12.5px] text-red-700">
              Pausado {agent.paused_by === "automático" ? "automáticamente" : `por ${agent.paused_by}`} · {fmtRelative(agent.paused_at)}
              {agent.pause_reason && <span className="block text-red-600/80">{agent.pause_reason}</span>}
            </div>
          )}
          <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-[12.5px]">
            <Detail label="Alias de la key"><code className="font-mono">{agent.key_alias}</code></Detail>
            <Detail label="Encargado">{agent.owner_name || "—"}{agent.owner_email && <span className="block text-mist-500">{agent.owner_email}</span>}</Detail>
            <Detail label="Modelos">{agent.models.join(", ")}</Detail>
            <Detail label="Límites">{agent.rpm_limit ? `${fmtNumber(agent.rpm_limit)} sol/min` : "Sin límite de solicitudes"} · {agent.tpm_limit ? `${fmtNumber(agent.tpm_limit)} tok/min` : "sin límite de tokens"}</Detail>
            <div className="col-span-2"><span className="eyebrow">Gasto del periodo</span><div className="mt-1.5"><BudgetBar usage={agent.usage} /></div>
              {agent.usage?.budget_reset_at && <p className="mt-1 text-[11.5px] text-mist-500">Se reinicia {new Date(agent.usage.budget_reset_at).toLocaleDateString("es-PE", { day: "numeric", month: "long" })}</p>}
            </div>
          </div>

          <div>
            <h4 className="mb-2 text-[13px] font-semibold text-ink-950">Actividad de las últimas 24 h</h4>
            {activityError && <p className="text-[12.5px] text-mist-500">{activityError}</p>}
            {!activity && !activityError && <Loader2 className="animate-spin text-mist-400" size={16} />}
            {activity && activity.length === 0 && <p className="text-[12.5px] text-mist-500">Sin llamadas en este periodo.</p>}
            {activity && activity.length > 0 && (
              <div className="max-h-56 overflow-y-auto rounded-lg border border-mist-200">
                <table className="w-full text-[12px]">
                  <thead className="sticky top-0 bg-mist-50 text-left text-mist-500">
                    <tr><th className="px-3 py-2 font-medium">Cuándo</th><th className="px-3 py-2 font-medium">Modelo</th><th className="px-3 py-2 font-medium">Estado</th><th className="px-3 py-2 text-right font-medium">Tokens</th><th className="px-3 py-2 text-right font-medium">Latencia</th><th className="px-3 py-2 text-right font-medium">Costo</th></tr>
                  </thead>
                  <tbody>
                    {activity.map((a, i) => (
                      <tr key={i} className="border-t border-mist-100">
                        <td className="px-3 py-1.5 text-mist-500">{fmtRelative(a.at)}</td>
                        <td className="px-3 py-1.5">{a.model}</td>
                        <td className="px-3 py-1.5"><Badge tone={a.status === "success" ? "good" : "critical"}>{STATUS_LABEL[a.status] || a.status}</Badge></td>
                        <td className="px-3 py-1.5 text-right tabular">{fmtNumber(a.prompt_tokens + a.completion_tokens)}</td>
                        <td className="px-3 py-1.5 text-right tabular">{fmtLatency(a.latency_ms)}</td>
                        <td className="px-3 py-1.5 text-right tabular">{fmtUSD(a.spend)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {agent.notifications?.length > 0 && (
            <div>
              <h4 className="mb-2 text-[13px] font-semibold text-ink-950">Historial</h4>
              <ul className="space-y-2">
                {agent.notifications.map((n) => (
                  <li key={n.id} className="flex gap-2.5 text-[12.5px]">
                    <span className="w-24 shrink-0 text-mist-400">{fmtRelative(n.created_at)}</span>
                    <span className="text-ink-700">{n.title}{n.message && <span className="text-mist-500"> · {n.message}</span>}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}

function Detail({ label, children }) {
  return (
    <div>
      <span className="eyebrow">{label}</span>
      <div className="mt-1 text-ink-950">{children}</div>
    </div>
  );
}

function AreaCard({ area, active, onClick, delay }) {
  return (
    <motion.button
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      onClick={onClick}
      className={`focus-ring card p-4 text-left transition hover:shadow-card ${active ? "border-ink-950 ring-1 ring-ink-950" : ""}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-[13.5px] font-semibold text-ink-950">{area.name}</p>
          <p className="mt-0.5 text-[12px] text-mist-500">
            {area.sistemas} {area.sistemas === 1 ? "sistema" : "sistemas"} · {area.agentes} {area.agentes === 1 ? "agente" : "agentes"}
          </p>
        </div>
        {area.agentes_pausados > 0 && <Badge tone="critical" dot>{area.agentes_pausados} en pausa</Badge>}
      </div>
      <div className="mt-4"><BudgetBar usage={area.usage} /></div>
    </motion.button>
  );
}

export default function Governance() {
  const { can } = useSession();
  const { toast, confirm } = useUI();
  const canGovern = can("govern");
  const [params, setParams] = useSearchParams();
  const [areas, setAreas] = useState(null);
  const [sistemas, setSistemas] = useState([]);
  const [agents, setAgents] = useState([]);
  const [unavailable, setUnavailable] = useState(false);
  const [areaFilter, setAreaFilter] = useState("");
  const [registerOpen, setRegisterOpen] = useState(false);
  const [sistemaOpen, setSistemaOpen] = useState(false);
  const [keyResult, setKeyResult] = useState(null);
  const [pausing, setPausing] = useState(null);
  const [editing, setEditing] = useState(null);

  const detailId = params.get("agente") ? Number(params.get("agente")) : null;
  const openDetail = (id) => setParams(id ? { agente: String(id) } : {});

  const load = useCallback(async () => {
    try {
      const [a, s, ag] = await Promise.all([govAreas(), govSistemas(), govAgents()]);
      setAreas(a);
      setSistemas(s);
      setAgents(ag);
      setUnavailable(false);
    } catch {
      setUnavailable(true);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, [load]);

  const grouped = useMemo(() => {
    const list = areaFilter ? agents.filter((a) => a.area_id === areaFilter) : agents;
    const bySistema = new Map();
    list.forEach((a) => {
      const key = a.sistema.id;
      if (!bySistema.has(key)) bySistema.set(key, { sistema: a.sistema, area: a.area, agents: [] });
      bySistema.get(key).agents.push(a);
    });
    return [...bySistema.values()];
  }, [agents, areaFilter]);

  const resume = async (agent) => {
    try {
      const data = await govResumeAgent(agent.id);
      toast(data.warning || `${agent.name} reactivado`, data.warning ? "info" : "success");
      load();
    } catch (err) {
      toast(errorMessage(err, "No se pudo reactivar el agente"), "error");
    }
  };

  const regenerate = async (agent) => {
    const ok = await confirm({
      title: `¿Regenerar la key de “${agent.name}”?`,
      description: "La key actual dejará de funcionar de inmediato y el encargado tendrá que usar la nueva.",
      confirmLabel: "Regenerar",
    });
    if (!ok) return;
    try {
      setKeyResult(await govRegenerateKey(agent.id));
      load();
    } catch (err) {
      toast(errorMessage(err, "No se pudo regenerar la key"), "error");
    }
  };

  const deregister = async (agent) => {
    const ok = await confirm({
      title: `¿Dar de baja “${agent.name}”?`,
      description: "Su key se elimina del gateway y deja de aparecer aquí. No se puede deshacer.",
      confirmLabel: "Dar de baja",
      danger: true,
    });
    if (!ok) return;
    try {
      await govDeleteAgent(agent.id);
      toast(`${agent.name} dado de baja`);
      load();
    } catch (err) {
      toast(errorMessage(err, "No se pudo dar de baja el agente"), "error");
    }
  };

  if (unavailable) {
    return (
      <div>
        <PageHeader title="Gobierno" description="Áreas, sistemas y agentes conectados al gateway" />
        <div className="mx-auto max-w-[1200px] px-8 py-8">
          <EmptyState
            icon={ServerOff}
            title="El servicio de gobierno no está disponible"
            description="Inicia el gateway y el servicio de gobierno para ver presupuestos, agentes conectados y avisos."
            action={<button onClick={load} className="btn-secondary"><RefreshCw size={14} /> Reintentar</button>}
          />
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Gobierno"
        description="Áreas, sistemas y agentes conectados al gateway"
        actions={
          canGovern && (
            <>
              <button onClick={() => setSistemaOpen(true)} className="btn-secondary"><Plus size={14} /> Sistema</button>
              <button onClick={() => setRegisterOpen(true)} className="btn-primary"><KeyRound size={14} /> Registrar agente</button>
            </>
          )
        }
      />
      <div className="mx-auto max-w-[1200px] space-y-6 px-8 py-8">
        {!areas ? (
          <div className="grid place-items-center py-20 text-mist-400"><Loader2 className="animate-spin" size={20} /></div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              {areas.map((a, i) => (
                <AreaCard key={a.id} area={a} delay={i * 0.04} active={areaFilter === a.id} onClick={() => setAreaFilter((f) => (f === a.id ? "" : a.id))} />
              ))}
            </div>

            {grouped.length === 0 && (
              <EmptyState icon={Landmark} title="Sin agentes registrados" compact
                description={canGovern ? "Registra un agente para emitir su virtual key." : "Aún no hay agentes conectados al gateway."} />
            )}

            {grouped.map(({ sistema, area, agents: list }) => (
              <section key={sistema.id} className="card overflow-hidden">
                <div className="flex items-center justify-between border-b border-mist-100 px-5 py-3">
                  <div className="flex items-baseline gap-2">
                    <h3 className="text-[13.5px] font-semibold text-ink-950">{sistema.name}</h3>
                    <span className="text-[12px] text-mist-500">{area.name}</span>
                  </div>
                  <span className="text-[12px] text-mist-500">{list.length} {list.length === 1 ? "agente" : "agentes"}</span>
                </div>
                <ul>
                  {list.map((a) => (
                    <li key={a.id} className="flex items-center gap-4 border-b border-mist-100 px-5 py-3 last:border-0 hover:bg-mist-50/60">
                      <button onClick={() => openDetail(a.id)} className="focus-ring min-w-0 flex-1 rounded text-left">
                        <span className="flex items-center gap-2">
                          <span className="truncate text-[13px] font-medium text-ink-950">{a.name}</span>
                          {a.status === "pausado" ? <Badge tone="critical" dot>Pausado</Badge> : <Badge tone="good" dot>Activo</Badge>}
                        </span>
                        <span className="mt-0.5 block truncate text-[12px] text-mist-500">
                          {a.status === "pausado" && a.pause_reason ? a.pause_reason : `Última actividad ${fmtRelative(a.usage?.last_active)}`}
                        </span>
                      </button>
                      <BudgetBar usage={a.usage} compact />
                      {canGovern && (
                        <div className="flex shrink-0 items-center gap-0.5">
                          {a.status === "pausado" ? (
                            <Tooltip label="Reactivar"><button onClick={() => resume(a)} className="btn-icon"><Play size={15} /></button></Tooltip>
                          ) : (
                            <Tooltip label="Pausar"><button onClick={() => setPausing(a)} className="btn-icon"><Pause size={15} /></button></Tooltip>
                          )}
                          <Tooltip label="Editar límites"><button onClick={() => setEditing(a)} className="btn-icon"><Pencil size={14} /></button></Tooltip>
                          <Tooltip label="Regenerar key">
                            <button
                              onClick={() => regenerate(a)}
                              className="btn-icon"
                            >
                              <RefreshCw size={14} />
                            </button>
                          </Tooltip>
                          <Tooltip label="Dar de baja">
                            <button
                              onClick={() => deregister(a)}
                              className="btn-icon hover:text-red-600"
                            >
                              <Trash2 size={14} />
                            </button>
                          </Tooltip>
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </>
        )}
      </div>

      <RegisterAgentModal
        open={registerOpen}
        sistemas={sistemas}
        onClose={() => setRegisterOpen(false)}
        onDone={(result) => { setRegisterOpen(false); setKeyResult(result); load(); }}
      />
      <SistemaModal open={sistemaOpen} areas={areas || []} onClose={() => setSistemaOpen(false)}
        onDone={() => { setSistemaOpen(false); toast("Sistema creado"); load(); }} />
      <KeyRevealModal result={keyResult} onClose={() => setKeyResult(null)} />
      <PauseModal agent={pausing} onClose={() => setPausing(null)} onDone={() => { toast(`${pausing.name} pausado`); setPausing(null); load(); }} />
      <LimitsModal agent={editing} onClose={() => setEditing(null)} onDone={() => { setEditing(null); toast("Límites actualizados"); load(); }} />
      <AgentDetailModal agentId={detailId} onClose={() => openDetail(null)} />
    </div>
  );
}

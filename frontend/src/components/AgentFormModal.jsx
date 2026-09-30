import { useEffect, useState } from "react";
import { Check, Loader2 } from "lucide-react";
import Modal from "./Modal";
import Tooltip from "./Tooltip";
import { AGENT_ICONS } from "../lib/icons";
import { listModels, listTools } from "../api/client";

const FALLBACK_MODELS = [{ name: "llama3.2:3b" }, { name: "mistral:latest" }];

const EMPTY = {
  name: "",
  icon: "bot",
  description: "",
  role_prompt: "",
  model: "llama3.2:3b",
  temperature: 0.4,
  tools: [],
};

export default function AgentFormModal({ open, initial, onSubmit, onClose }) {
  const [models, setModels] = useState([]);
  const [tools, setTools] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    setForm(initial ? { ...EMPTY, ...initial } : EMPTY);
    listModels()
      .then((m) => setModels(m.filter((x) => !x.embedding).length ? m.filter((x) => !x.embedding) : FALLBACK_MODELS))
      .catch(() => setModels(FALLBACK_MODELS));
    listTools().then(setTools).catch(() => setTools([]));
  }, [open, initial]);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e?.target ? e.target.value : e }));

  const toggleTool = (name) =>
    setForm((f) => ({ ...f, tools: f.tools.includes(name) ? f.tools.filter((t) => t !== name) : [...f.tools, name] }));

  const modelOptions = models.some((m) => m.name === form.model) ? models : [{ name: form.model }, ...models];

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const { name, icon, description, role_prompt, model, temperature, tools: selected } = form;
      await onSubmit({ name, icon, description, role_prompt, model, temperature, tools: selected });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      size="lg"
      title={initial ? "Editar agente" : "Nuevo agente"}
      subtitle={initial ? "Los cambios aplican a las próximas conversaciones." : "Configura su rol, modelo y capacidades."}
    >
      <form onSubmit={submit} className="space-y-5 px-6 py-5">
        <div>
          <span className="label">Ícono</span>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(AGENT_ICONS).map(([key, Icon]) => (
              <button
                type="button"
                key={key}
                onClick={() => set("icon")(key)}
                className={`focus-ring grid h-9 w-9 place-items-center rounded-lg border transition ${
                  form.icon === key ? "border-ink-950 bg-ink-950 text-white" : "border-mist-200 text-ink-700 hover:border-mist-300 hover:bg-mist-50"
                }`}
                aria-label={key}
              >
                <Icon size={16} strokeWidth={1.75} />
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="agent-name">Nombre</label>
            <input id="agent-name" required minLength={2} value={form.name} onChange={set("name")} placeholder="Ej. Analista de Contratos" className="input" />
          </div>
          <div>
            <label className="label" htmlFor="agent-desc">Descripción</label>
            <input id="agent-desc" value={form.description} onChange={set("description")} placeholder="¿Para qué sirve?" className="input" />
          </div>
        </div>

        <div>
          <label className="label" htmlFor="agent-prompt">Instrucciones del sistema</label>
          <textarea
            id="agent-prompt"
            required
            minLength={5}
            rows={5}
            value={form.role_prompt}
            onChange={set("role_prompt")}
            placeholder="Eres un agente que… Responde siempre en español y…"
            className="input resize-y leading-relaxed"
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="agent-model">Modelo</label>
            <select id="agent-model" value={form.model} onChange={set("model")} className="input font-mono text-[13px]">
              {modelOptions.map((m) => (
                <option key={m.name} value={m.name}>{m.name}</option>
              ))}
            </select>
          </div>
          <div>
            <div className="label flex items-center justify-between">
              <span>Temperatura</span>
              <span className="font-mono text-ink-950">{Number(form.temperature).toFixed(1)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={form.temperature}
              onChange={(e) => set("temperature")(parseFloat(e.target.value))}
              className="mt-2 w-full accent-accent"
            />
            <div className="mt-0.5 flex justify-between text-[11px] text-mist-400">
              <span>Preciso</span>
              <span>Creativo</span>
            </div>
          </div>
        </div>

        {tools.length > 0 && (
          <div>
            <span className="label">Herramientas</span>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              {tools.map((t) => {
                const on = form.tools.includes(t.name);
                return (
                  <Tooltip key={t.name} label={t.description}>
                    <button
                      type="button"
                      onClick={() => toggleTool(t.name)}
                      className={`focus-ring flex items-center justify-between gap-2 rounded-lg border px-3 py-2.5 text-left transition ${
                        on ? "border-accent bg-accent-50" : "border-mist-200 hover:border-mist-300"
                      }`}
                    >
                      <span className="truncate font-mono text-[12px] text-ink-950">{t.name}</span>
                      <span className={`grid h-4 w-4 shrink-0 place-items-center rounded ${on ? "bg-accent text-white" : "border border-mist-300"}`}>
                        {on && <Check size={11} strokeWidth={3} />}
                      </span>
                    </button>
                  </Tooltip>
                );
              })}
            </div>
          </div>
        )}

        <div className="-mx-6 -mb-5 flex justify-end gap-2 border-t border-mist-100 bg-mist-50/60 px-6 py-4">
          <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
          <button type="submit" disabled={saving} className="btn-primary">
            {saving && <Loader2 size={14} className="animate-spin" />}
            {initial ? "Guardar cambios" : "Crear agente"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

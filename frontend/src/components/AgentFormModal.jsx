import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { listModels, listTools } from "../api/client";

const EMOJI_PRESETS = ["🤖", "🛠️", "📊", "📝", "🎓", "🧭", "💬", "🔎", "⚖️", "📦"];

export default function AgentFormModal({ initial, onSubmit, onClose }) {
  const [models, setModels] = useState([]);
  const [tools, setTools] = useState([]);
  const [form, setForm] = useState(
    initial || {
      name: "",
      avatar_emoji: "🤖",
      description: "",
      role_prompt: "",
      model: "llama3.2:3b",
      temperature: 0.4,
      tools: [],
    }
  );
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    listModels().then((m) => setModels(m.length ? m : [{ name: "llama3.2:3b" }, { name: "mistral:latest" }])).catch(() =>
      setModels([{ name: "llama3.2:3b" }, { name: "mistral:latest" }])
    );
    listTools().then(setTools).catch(() => setTools([]));
  }, []);

  const toggleTool = (name) => {
    setForm((f) => ({
      ...f,
      tools: f.tools.includes(name) ? f.tools.filter((t) => t !== name) : [...f.tools, name],
    }));
  };

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSubmit(form);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-ink-950/40 px-4 backdrop-blur-sm">
      <div className="max-h-[88vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-card animate-fadeUp">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-[15px] font-semibold text-ink-950">
            {initial ? "Editar agente" : "Nuevo agente"}
          </h2>
          <button onClick={onClose} className="focus-ring rounded-full p-1.5 text-mist-400 hover:bg-mist-100">
            <X size={16} />
          </button>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <div className="flex gap-3">
            <div>
              <label className="mb-1.5 block text-[12px] font-medium text-mist-500">Ícono</label>
              <div className="flex flex-wrap gap-1 rounded-xl border border-mist-200 p-1.5">
                {EMOJI_PRESETS.map((e) => (
                  <button
                    type="button"
                    key={e}
                    onClick={() => setForm((f) => ({ ...f, avatar_emoji: e }))}
                    className={`grid h-8 w-8 place-items-center rounded-lg text-base hover:bg-mist-100 ${
                      form.avatar_emoji === e ? "bg-tcs-50 ring-1 ring-tcs" : ""
                    }`}
                  >
                    {e}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex-1">
              <label className="mb-1.5 block text-[12px] font-medium text-mist-500">Nombre del agente</label>
              <input
                required
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="Ej. Analista de Contratos"
                className="focus-ring w-full rounded-xl border border-mist-200 px-3 py-2.5 text-[13.5px]"
              />
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-[12px] font-medium text-mist-500">Descripción corta</label>
            <input
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              placeholder="¿Para qué sirve este agente?"
              className="focus-ring w-full rounded-xl border border-mist-200 px-3 py-2.5 text-[13.5px]"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-[12px] font-medium text-mist-500">
              Prompt de sistema (rol y reglas de comportamiento)
            </label>
            <textarea
              required
              rows={4}
              value={form.role_prompt}
              onChange={(e) => setForm((f) => ({ ...f, role_prompt: e.target.value }))}
              placeholder="Eres un agente que..."
              className="focus-ring w-full resize-none rounded-xl border border-mist-200 px-3 py-2.5 text-[13.5px]"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1.5 block text-[12px] font-medium text-mist-500">Modelo</label>
              <select
                value={form.model}
                onChange={(e) => setForm((f) => ({ ...f, model: e.target.value }))}
                className="focus-ring w-full rounded-xl border border-mist-200 bg-white px-3 py-2.5 text-[13.5px]"
              >
                {models.map((m) => (
                  <option key={m.name} value={m.name}>{m.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-[12px] font-medium text-mist-500">
                Temperatura: <span className="tabular text-ink-950">{form.temperature}</span>
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={form.temperature}
                onChange={(e) => setForm((f) => ({ ...f, temperature: parseFloat(e.target.value) }))}
                className="w-full accent-tcs"
              />
            </div>
          </div>

          {tools.length > 0 && (
            <div>
              <label className="mb-1.5 block text-[12px] font-medium text-mist-500">Herramientas (function calling)</label>
              <div className="space-y-1.5">
                {tools.map((t) => (
                  <label key={t.name} className="flex cursor-pointer items-start gap-2.5 rounded-xl border border-mist-200 px-3 py-2.5 hover:bg-mist-50">
                    <input
                      type="checkbox"
                      checked={form.tools.includes(t.name)}
                      onChange={() => toggleTool(t.name)}
                      className="mt-0.5 accent-tcs"
                    />
                    <span>
                      <span className="block text-[13px] font-medium text-ink-950">{t.name}</span>
                      <span className="block text-[11.5px] text-mist-500">{t.description}</span>
                    </span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="focus-ring rounded-xl border border-mist-200 px-4 py-2.5 text-[13px] font-medium text-ink-950 hover:bg-mist-50">
              Cancelar
            </button>
            <button type="submit" disabled={saving} className="focus-ring rounded-xl bg-ink-950 px-4 py-2.5 text-[13px] font-medium text-white hover:bg-ink-800 disabled:opacity-50">
              {saving ? "Guardando..." : initial ? "Guardar cambios" : "Crear agente"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

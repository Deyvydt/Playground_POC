import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Copy, Loader2, Play, Plus, X, CircleAlert, Sparkles } from "lucide-react";
import PageHeader from "../components/PageHeader";
import Tooltip from "../components/Tooltip";
import TracePanel from "../components/TracePanel";
import { AgentIcon } from "../lib/icons";
import { Markdown } from "../lib/markdown";
import { listAgents, streamOrchestration } from "../api/client";
import { useUI } from "../context/UIContext";
import { fmtLatency, fmtNumber } from "../lib/format";

const TEMPLATES = [
  {
    label: "Análisis de margen",
    agents: ["Analista de Datos", "Redactor de Reportes"],
    text: "Nuestro margen operativo bajó 4 puntos este trimestre en la cuenta de retail: los ingresos fueron 2.4M y los costos subieron de 1.9M a 2.0M. Necesito entender por qué y un resumen para el comité.",
  },
  {
    label: "Incidencia a comunicado",
    agents: ["Soporte TI", "Redactor de Reportes"],
    text: "Revisa el estado del ticket TCS-4471 y prepara un comunicado breve para el cliente explicando la situación y los próximos pasos.",
  },
];

function Connector({ state }) {
  return (
    <div className="relative mx-1 hidden h-px w-10 shrink-0 bg-mist-300 sm:block">
      {state === "flow" && (
        <motion.span
          className="absolute -top-[3px] h-[7px] w-[7px] rounded-full bg-accent"
          animate={{ left: ["0%", "100%"] }}
          transition={{ duration: 0.9, repeat: Infinity, ease: "easeInOut" }}
        />
      )}
      {state === "done" && <span className="absolute inset-0 bg-ink-950" />}
    </div>
  );
}

function Node({ index, agentId, agents, status, onChange, onRemove, removable, disabled }) {
  const agent = agents.find((a) => a.id === agentId);
  const ring = {
    running: "border-accent shadow-glow",
    done: "border-ink-950",
    error: "border-red-400",
  }[status] || "border-mist-200";

  return (
    <motion.div layout initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
      className={`relative w-60 shrink-0 rounded-xl border bg-white p-3.5 transition-all ${ring}`}
    >
      <div className="flex items-center justify-between">
        <span className="font-mono text-[10.5px] text-mist-400">PASO {index + 1}</span>
        <span className="flex h-5 items-center">
          {status === "running" && <Loader2 size={14} className="animate-spin text-accent" />}
          {status === "done" && <span className="grid h-5 w-5 place-items-center rounded-full bg-ink-950 text-white"><Check size={11} strokeWidth={3} /></span>}
          {status === "error" && <CircleAlert size={15} className="text-red-500" />}
          {!status && removable && !disabled && (
            <Tooltip label="Quitar paso">
              <button onClick={onRemove} className="btn-icon h-6 w-6"><X size={13} /></button>
            </Tooltip>
          )}
        </span>
      </div>
      <div className="mt-2.5 flex items-center gap-2.5">
        <AgentIcon name={agent?.icon} size="md" tone={status === "done" || status === "running" ? "dark" : "light"} />
        <select
          value={agentId || ""}
          disabled={disabled}
          onChange={(e) => onChange(Number(e.target.value))}
          className="focus-ring min-w-0 flex-1 cursor-pointer truncate rounded-md bg-transparent py-1 text-[13px] font-medium text-ink-950 disabled:cursor-default"
        >
          {agents.map((a) => (
            <option key={a.id} value={a.id}>{a.name}</option>
          ))}
        </select>
      </div>
    </motion.div>
  );
}

export default function Flows() {
  const { toast } = useUI();
  const [agents, setAgents] = useState([]);
  const [pipeline, setPipeline] = useState([]);
  const [input, setInput] = useState(TEMPLATES[0].text);
  const [statuses, setStatuses] = useState({});
  const [steps, setSteps] = useState([]);
  const [running, setRunning] = useState(false);
  const [copied, setCopied] = useState(false);

  const byName = (list, name) => list.find((a) => a.name === name)?.id;

  useEffect(() => {
    listAgents().then((data) => {
      const active = data.filter((a) => a.status === "active");
      setAgents(active);
      const preset = TEMPLATES[0].agents.map((n) => byName(active, n)).filter(Boolean);
      setPipeline(preset.length >= 2 ? preset : active.slice(0, 2).map((a) => a.id));
    });
  }, []);

  const applyTemplate = (t) => {
    setInput(t.text);
    const ids = t.agents.map((n) => byName(agents, n)).filter(Boolean);
    if (ids.length >= 2) setPipeline(ids);
    reset();
  };

  const reset = () => {
    setStatuses({});
    setSteps([]);
  };

  const run = async () => {
    reset();
    setRunning(true);
    try {
      await streamOrchestration({ input_text: input, pipeline }, (ev) => {
        if (ev.event === "start") setStatuses((s) => ({ ...s, [ev.index]: "running" }));
        if (ev.event === "step") {
          setStatuses((s) => ({ ...s, [ev.index]: "done" }));
          setSteps((s) => [...s, ev.step]);
        }
        if (ev.event === "error") {
          setStatuses((s) => ({ ...s, [ev.index]: "error" }));
          toast(ev.message, "error");
        }
      });
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setRunning(false);
    }
  };

  const connectorState = (i) => {
    if (statuses[i] === "done" && statuses[i + 1] === "running") return "flow";
    if (statuses[i] === "done" && statuses[i + 1]) return "done";
    return null;
  };

  const finished = steps.length === pipeline.length && steps.length > 0;
  const final = finished ? steps[steps.length - 1] : null;
  const totalTokens = steps.reduce((acc, s) => acc + (s.tokens || 0), 0);
  const totalLatency = steps.reduce((acc, s) => acc + s.latency_ms, 0);

  return (
    <div>
      <PageHeader title="Flujos" description="La respuesta de cada agente alimenta al siguiente" />
      <div className="mx-auto max-w-[1200px] space-y-5 px-8 py-8">
        <div className="card p-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <label htmlFor="flow-input" className="text-[13.5px] font-semibold text-ink-950">Solicitud</label>
            <div className="flex flex-wrap gap-1.5">
              {TEMPLATES.map((t) => (
                <button key={t.label} onClick={() => applyTemplate(t)} disabled={running}
                  className="focus-ring inline-flex items-center gap-1.5 rounded-full border border-mist-200 px-2.5 py-1 text-[12px] text-ink-700 transition hover:border-mist-300 hover:bg-mist-50">
                  <Sparkles size={12} className="text-accent" /> {t.label}
                </button>
              ))}
            </div>
          </div>
          <textarea id="flow-input" rows={3} value={input} onChange={(e) => setInput(e.target.value)} disabled={running} className="input mt-3 resize-none leading-relaxed" />
        </div>

        <div className="card dot-grid overflow-hidden">
          <div className="flex items-center justify-between border-b border-mist-100 bg-white px-5 py-3.5">
            <h3 className="text-[13.5px] font-semibold text-ink-950">Secuencia</h3>
            <button onClick={run} disabled={running || pipeline.length < 2 || !input.trim()} className="btn-accent">
              {running ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
              {running ? "Ejecutando…" : "Ejecutar flujo"}
            </button>
          </div>
          <div className="flex items-center overflow-x-auto px-6 py-8">
            <AnimatePresence initial={false}>
              {pipeline.map((agentId, idx) => (
                <div key={idx} className="flex items-center">
                  <Node
                    index={idx}
                    agentId={agentId}
                    agents={agents}
                    status={statuses[idx]}
                    disabled={running}
                    removable={pipeline.length > 2}
                    onChange={(id) => { setPipeline((p) => p.map((v, i) => (i === idx ? id : v))); reset(); }}
                    onRemove={() => { setPipeline((p) => p.filter((_, i) => i !== idx)); reset(); }}
                  />
                  {idx < pipeline.length - 1 && <Connector state={connectorState(idx)} />}
                </div>
              ))}
            </AnimatePresence>
            {pipeline.length < 5 && !running && (
              <Tooltip label="Agregar paso">
                <button
                  onClick={() => { setPipeline((p) => [...p, agents[0]?.id]); reset(); }}
                  className="focus-ring ml-4 grid h-10 w-10 shrink-0 place-items-center rounded-full border border-dashed border-mist-400 bg-white text-mist-500 transition hover:border-accent hover:text-accent"
                >
                  <Plus size={16} />
                </button>
              </Tooltip>
            )}
          </div>
        </div>

        <AnimatePresence>
          {final && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="overflow-hidden rounded-xl bg-ink-950 text-white">
              <div className="flex items-center justify-between border-b border-white/10 px-5 py-3.5">
                <div>
                  <p className="text-[13.5px] font-semibold">Resultado final</p>
                  <p className="font-mono text-[11.5px] text-white/45">
                    {steps.length} agentes · {fmtLatency(totalLatency)} · {fmtNumber(totalTokens)} tokens
                  </p>
                </div>
                <Tooltip label={copied ? "Copiado" : "Copiar resultado"}>
                  <button
                    onClick={() => { navigator.clipboard?.writeText(final.output); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
                    className="focus-ring grid h-8 w-8 place-items-center rounded-lg text-white/60 hover:bg-white/10 hover:text-white"
                  >
                    {copied ? <Check size={15} /> : <Copy size={15} />}
                  </button>
                </Tooltip>
              </div>
              <div className="px-5 py-4 text-[14px] leading-relaxed text-white/90 [&_code]:bg-white/10">
                <Markdown text={final.output} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {steps.length === 0 && !running && (
          <p className="py-6 text-center text-[13px] text-mist-400">Ejecuta el flujo para ver la respuesta de cada agente.</p>
        )}

        {steps.length > 0 && (
          <div className="space-y-3">
            <p className="eyebrow">Detalle por paso</p>
            {steps.map((s, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="card p-5">
                <div className="flex items-center gap-3">
                  <AgentIcon name={s.icon} size="md" />
                  <div className="flex-1">
                    <p className="text-[13.5px] font-semibold text-ink-950">{s.agent_name}</p>
                    <p className="font-mono text-[11.5px] text-mist-400">Paso {i + 1} · {fmtLatency(s.latency_ms)} · {fmtNumber(s.tokens)} tokens</p>
                  </div>
                </div>
                <div className="mt-3 rounded-lg bg-mist-50 px-4 py-3 text-[13.5px] leading-relaxed text-ink-800">
                  <Markdown text={s.output} />
                </div>
                <TracePanel trace={s.trace} />
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

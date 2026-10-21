import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CircleAlert, CircleCheck, Code2, FlaskConical, Loader2, Play, Users } from "lucide-react";
import PageHeader from "../components/PageHeader";
import Badge from "../components/Badge";
import EmptyState from "../components/EmptyState";
import { errorMessage, labRun } from "../api/client";
import { fmtNumber } from "../lib/format";

const SISTEMAS = [
  {
    id: "talentia",
    name: "Talentia",
    area: "Recursos Humanos",
    icon: Users,
    description: "Analiza un CV frente a una vacante, puntúa el ajuste y prepara la entrevista o el mensaje de rechazo.",
    fields: [
      { key: "vacante", label: "Vacante", rows: 3, example: "Desarrollador Java Senior. Requisitos: 5+ años con Java 17, Quarkus, microservicios y PostgreSQL. Deseable: Kubernetes." },
      { key: "cv", label: "CV del candidato", rows: 6, example: "Ana Torres. Ingeniera de sistemas. 6 años como desarrolladora backend Java (Spring Boot y Quarkus). Diseñó microservicios con PostgreSQL y Kafka en banca. Certificada en Kubernetes (CKAD)." },
    ],
    output: [
      { key: "analisis_cv", label: "Análisis del CV" },
      { key: "puntaje", label: "Puntaje de ajuste" },
      { key: "resultado", label: "Resultado" },
    ],
  },
  {
    id: "agentfactory",
    name: "AgentFactory",
    area: "Desarrollo",
    icon: Code2,
    description: "Genera código Java/Quarkus a partir de un requerimiento, lo revisa en rondas y produce tests y documentación.",
    fields: [
      { key: "requerimiento", label: "Requerimiento", rows: 5, example: "Endpoint REST en Quarkus que reciba un monto y una moneda (PEN o USD) y devuelva el monto convertido a la otra moneda con un tipo de cambio fijo de 3.75." },
    ],
    output: [
      { key: "codigo", label: "Código", mono: true },
      { key: "observaciones", label: "Observaciones de la revisión" },
      { key: "tests", label: "Tests", mono: true },
      { key: "documentacion", label: "Documentación" },
    ],
  },
];

const initialInputs = () =>
  Object.fromEntries(SISTEMAS.map((s) => [s.id, Object.fromEntries(s.fields.map((f) => [f.key, f.example]))]));

function Step({ step, index }) {
  const ok = step.estado === "ok";
  return (
    <motion.li
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06 }}
      className="relative pl-8"
    >
      <span className={`absolute left-0 top-0.5 grid h-5 w-5 place-items-center rounded-full ${ok ? "bg-ink-950 text-white" : "bg-red-50 text-red-600 ring-1 ring-red-100"}`}>
        {ok ? <CircleCheck size={12} /> : <CircleAlert size={12} />}
      </span>
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-[12.5px] font-medium text-ink-950">{step.nodo}</span>
        {ok ? (
          <span className="text-[11.5px] tabular text-mist-500">
            {fmtNumber(step.tokens_entrada)} entrada · {fmtNumber(step.tokens_salida)} salida
          </span>
        ) : (
          <Badge tone="critical">{step.mensaje}</Badge>
        )}
      </div>
      {step.salida && (
        <p className="mt-1.5 whitespace-pre-wrap rounded-lg border border-mist-200 bg-mist-50 p-3 text-[12.5px] leading-relaxed text-ink-700">{step.salida}</p>
      )}
    </motion.li>
  );
}

export default function Lab() {
  const [sistemaId, setSistemaId] = useState("talentia");
  const [inputs, setInputs] = useState(initialInputs);
  const [running, setRunning] = useState(false);
  const [run, setRun] = useState(null);
  const [error, setError] = useState("");

  const sistema = SISTEMAS.find((s) => s.id === sistemaId);
  const values = inputs[sistemaId];
  const ready = sistema.fields.every((f) => values[f.key]?.trim());

  const select = (id) => {
    if (running) return;
    setSistemaId(id);
    setRun(null);
    setError("");
  };

  const execute = async (e) => {
    e.preventDefault();
    setRunning(true);
    setRun(null);
    setError("");
    try {
      setRun(await labRun(sistemaId, values));
    } catch (err) {
      setError(errorMessage(err, "No se pudo ejecutar el grafo. Verifica que el laboratorio esté en línea."));
    } finally {
      setRunning(false);
    }
  };

  return (
    <div>
      <PageHeader title="Laboratorio" description="Grafos de prueba: cada nodo es un agente con su propia key" />
      <div className="mx-auto grid max-w-[1200px] gap-6 px-8 py-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <form onSubmit={execute} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            {SISTEMAS.map((s) => {
              const Icon = s.icon;
              const active = s.id === sistemaId;
              return (
                <button
                  type="button"
                  key={s.id}
                  onClick={() => select(s.id)}
                  className={`focus-ring card p-4 text-left transition hover:shadow-card ${active ? "border-ink-950 ring-1 ring-ink-950" : ""}`}
                >
                  <span className={`grid h-8 w-8 place-items-center rounded-lg ${active ? "bg-ink-950 text-white" : "bg-mist-100 text-ink-700"}`}>
                    <Icon size={16} />
                  </span>
                  <p className="mt-3 text-[13.5px] font-semibold text-ink-950">{s.name}</p>
                  <p className="text-[12px] text-mist-500">{s.area}</p>
                </button>
              );
            })}
          </div>
          <p className="text-[12.5px] leading-relaxed text-mist-500">{sistema.description}</p>
          {sistema.fields.map((f) => (
            <div key={f.key}>
              <label className="label" htmlFor={`lab-${f.key}`}>{f.label}</label>
              <textarea
                id={`lab-${f.key}`}
                rows={f.rows}
                className="input resize-y"
                value={values[f.key]}
                onChange={(e) => setInputs((all) => ({ ...all, [sistemaId]: { ...all[sistemaId], [f.key]: e.target.value } }))}
              />
            </div>
          ))}
          <button type="submit" disabled={running || !ready} className="btn-primary w-full">
            {running ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            {running ? "Ejecutando… puede tardar unos minutos" : "Ejecutar grafo"}
          </button>
          {error && <p className="text-[12.5px] text-red-600">{error}</p>}
        </form>

        <div className="space-y-4">
          <AnimatePresence mode="wait">
            {!run && !running && (
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <EmptyState icon={FlaskConical} title="Sin ejecuciones todavía" description="Ejecuta el grafo para ver la entrada y la salida de cada nodo, y los tokens que consumió." />
              </motion.div>
            )}
            {running && (
              <motion.div key="running" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="card grid place-items-center gap-3 py-16 text-center">
                <Loader2 className="animate-spin text-accent" size={20} />
                <p className="text-[13px] text-mist-500">Los nodos se ejecutan en orden; cada uno llama al modelo con su propia key.</p>
              </motion.div>
            )}
            {run && (
              <motion.div key={run.run_id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
                {run.error && (
                  <div className="flex gap-2.5 rounded-lg border border-red-100 bg-red-50 p-3 text-[12.5px] text-red-700">
                    <CircleAlert size={16} className="mt-0.5 shrink-0" /> El grafo se detuvo: {run.error}
                  </div>
                )}
                <section className="card p-5">
                  <div className="mb-4 flex items-center justify-between">
                    <h3 className="text-[13.5px] font-semibold text-ink-950">Recorrido nodo por nodo</h3>
                    <span className="font-mono text-[11px] text-mist-400">{run.run_id.slice(0, 8)}</span>
                  </div>
                  <ol className="space-y-4 border-l border-mist-200 pl-0 [&>li]:-ml-2.5">
                    {run.trace.map((step, i) => <Step key={i} step={step} index={i} />)}
                  </ol>
                </section>
                {!run.error && (
                  <section className="card divide-y divide-mist-100">
                    {sistema.output.filter((o) => run.resultado[o.key] !== undefined && run.resultado[o.key] !== "").map((o) => (
                      <div key={o.key} className="p-5">
                        <p className="eyebrow">{o.label}</p>
                        <div className={`mt-2 whitespace-pre-wrap text-[13px] leading-relaxed text-ink-950 ${o.mono ? "font-mono text-[12px]" : ""}`}>
                          {String(run.resultado[o.key])}
                        </div>
                      </div>
                    ))}
                  </section>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

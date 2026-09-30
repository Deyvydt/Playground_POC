import { useEffect, useState } from "react";
import { ArrowRight, Plus, X, Workflow, Play } from "lucide-react";
import TopBar from "../components/TopBar";
import TracePanel from "../components/TracePanel";
import EmptyState from "../components/EmptyState";
import { listAgents, runOrchestration } from "../api/client";

export default function MultiAgentFlow() {
  const [agents, setAgents] = useState([]);
  const [pipeline, setPipeline] = useState([]);
  const [input, setInput] = useState(
    "Nuestro margen operativo bajó 4 puntos este trimestre en la cuenta de retail. Necesito entender por qué y un resumen para el comité."
  );
  const [steps, setSteps] = useState([]);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    listAgents().then((data) => {
      setAgents(data);
      if (data.length >= 2) setPipeline([data[0].id, data[1].id]);
    });
  }, []);

  const updateStep = (idx, agentId) => {
    setPipeline((p) => p.map((v, i) => (i === idx ? Number(agentId) : v)));
  };
  const addStep = () => setPipeline((p) => [...p, agents[0]?.id]);
  const removeStep = (idx) => setPipeline((p) => p.filter((_, i) => i !== idx));

  const run = async () => {
    setRunning(true);
    setSteps([]);
    try {
      const res = await runOrchestration({ input_text: input, pipeline });
      setSteps(res.steps);
    } catch {
      alert("No se pudo ejecutar el flujo. Verifica que Ollama esté activo.");
    } finally {
      setRunning(false);
    }
  };

  const agentById = (id) => agents.find((a) => a.id === id);

  return (
    <div>
      <TopBar title="Flujo multi-agente" description="Encadena agentes: la salida de uno alimenta la entrada del siguiente" />
      <div className="mx-auto max-w-5xl space-y-6 px-8 py-8">
        <div className="rounded-2xl border border-mist-200 bg-white p-5">
          <label className="mb-1.5 block text-[12px] font-medium text-mist-500">Escenario de negocio (entrada inicial)</label>
          <textarea
            rows={3}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="focus-ring w-full resize-none rounded-xl border border-mist-200 px-3.5 py-2.5 text-[13.5px]"
          />
        </div>

        <div className="rounded-2xl border border-mist-200 bg-white p-5">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-[13.5px] font-semibold text-ink-950">
              <Workflow size={15} className="text-tcs" /> Pipeline de agentes
            </h3>
            <button onClick={addStep} className="focus-ring inline-flex items-center gap-1 text-[12.5px] font-medium text-tcs-dark hover:underline">
              <Plus size={13} /> Agregar paso
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {pipeline.map((agentId, idx) => (
              <div key={idx} className="flex items-center gap-3">
                <div className="flex items-center gap-2 rounded-xl border border-mist-200 bg-mist-50 px-3 py-2.5">
                  <span className="text-lg">{agentById(agentId)?.avatar_emoji}</span>
                  <select
                    value={agentId || ""}
                    onChange={(e) => updateStep(idx, e.target.value)}
                    className="focus-ring bg-transparent text-[13px] font-medium text-ink-950"
                  >
                    {agents.map((a) => (
                      <option key={a.id} value={a.id}>{a.name}</option>
                    ))}
                  </select>
                  {pipeline.length > 2 && (
                    <button onClick={() => removeStep(idx)} className="text-mist-400 hover:text-red-600"><X size={13} /></button>
                  )}
                </div>
                {idx < pipeline.length - 1 && <ArrowRight size={16} className="text-mist-300" />}
              </div>
            ))}
          </div>

          <button
            onClick={run}
            disabled={running || pipeline.length < 2}
            className="focus-ring mt-5 inline-flex items-center gap-2 rounded-xl bg-ink-950 px-5 py-2.5 text-[13px] font-semibold text-white hover:bg-ink-800 disabled:opacity-40"
          >
            <Play size={14} /> {running ? "Ejecutando flujo…" : "Ejecutar flujo"}
          </button>
        </div>

        {steps.length === 0 ? (
          <EmptyState icon={Workflow} title="Aún no se ha ejecutado ningún flujo" description="Configura el pipeline y presiona “Ejecutar flujo” para ver cómo colaboran los agentes." />
        ) : (
          <div className="space-y-4">
            {steps.map((s, i) => (
              <div key={i} className="rounded-2xl border border-mist-200 bg-white p-5 animate-fadeUp">
                <div className="flex items-center gap-2.5">
                  <span className="grid h-9 w-9 place-items-center rounded-xl bg-mist-100 text-lg">{s.avatar_emoji}</span>
                  <div>
                    <p className="text-[13.5px] font-semibold text-ink-950">Paso {i + 1} · {s.agent_name}</p>
                    <p className="text-[11px] text-mist-400">{s.latency_ms} ms</p>
                  </div>
                </div>
                <p className="mt-3 whitespace-pre-wrap rounded-xl bg-mist-50 p-3.5 text-[13.5px] leading-relaxed text-ink-800">{s.output}</p>
                <TracePanel trace={s.trace} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

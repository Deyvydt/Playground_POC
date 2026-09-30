import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { FileText, Search, Wrench, MessageCircle, ChevronRight, Cpu, CircleAlert } from "lucide-react";

const ICONS = {
  system_prompt: FileText,
  retrieval: Search,
  model_call: Cpu,
  tool_call: Wrench,
  final_answer: MessageCircle,
};

const LABELS = {
  system_prompt: "Instrucciones del sistema",
  retrieval: "Búsqueda en conocimiento",
  model_call: "Llamada al modelo",
  tool_call: "Herramienta",
  final_answer: "Respuesta final",
};

function Json({ value }) {
  return (
    <pre className="whitespace-pre-wrap break-words rounded-md bg-mist-50 p-2.5 font-mono text-[11.5px] leading-relaxed text-ink-800 ring-1 ring-inset ring-mist-200">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

function StepDetail({ step }) {
  if (step.type === "retrieval") {
    if (step.error) return <p className="text-[12px] text-amber-700">{step.error}</p>;
    return (
      <div className="space-y-1.5">
        {step.detail.map((d, i) => (
          <div key={i} className="flex gap-2.5 rounded-md bg-mist-50 px-2.5 py-2 text-[12px] text-ink-800 ring-1 ring-inset ring-mist-200">
            <span className="shrink-0 font-mono text-[11px] font-medium text-accent-dark">{Number(d.score).toFixed(2)}</span>
            <span className="line-clamp-3">{d.preview}…</span>
          </div>
        ))}
      </div>
    );
  }
  if (step.type === "tool_call") {
    return (
      <div className="grid gap-2 sm:grid-cols-2">
        <div>
          <p className="mb-1 text-[11px] text-mist-500">Entrada</p>
          <Json value={step.detail.argumentos} />
        </div>
        <div>
          <p className="mb-1 text-[11px] text-mist-500">Resultado</p>
          <Json value={step.detail.resultado} />
        </div>
      </div>
    );
  }
  if (step.type === "model_call") {
    const d = step.detail;
    return (
      <div className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-[11.5px] text-mist-500">
        <span>ronda {d.ronda}</span>
        <span>{d.tokens_entrada} tok entrada</span>
        <span>{d.tokens_salida} tok salida</span>
        <span>{d.latencia_ms} ms</span>
      </div>
    );
  }
  return <p className="line-clamp-6 whitespace-pre-wrap text-[12px] leading-relaxed text-ink-700">{String(step.detail)}</p>;
}

export default function TracePanel({ trace = [], defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  if (!trace.length) return null;
  const tools = trace.filter((s) => s.type === "tool_call").length;
  const retrieval = trace.some((s) => s.type === "retrieval" && !s.error);

  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen((v) => !v)}
        className="focus-ring inline-flex items-center gap-1.5 rounded-md py-0.5 text-[11.5px] font-medium text-mist-500 hover:text-ink-950"
        aria-expanded={open}
      >
        <ChevronRight size={13} className={`transition-transform ${open ? "rotate-90" : ""}`} />
        Ver razonamiento · {trace.length} pasos
        {retrieval && <span className="rounded bg-mist-100 px-1.5 text-[10.5px]">conocimiento</span>}
        {tools > 0 && <span className="rounded bg-accent-50 px-1.5 text-[10.5px] text-accent-dark">{tools} herramienta{tools > 1 ? "s" : ""}</span>}
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22 }}
            className="overflow-hidden"
          >
            <div className="mt-2 rounded-xl border border-mist-200 bg-white p-3.5">
              {trace.map((step, i) => {
                const Icon = step.error ? CircleAlert : ICONS[step.type] || FileText;
                return (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -4 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className="flex gap-3"
                  >
                    <div className="flex flex-col items-center">
                      <span
                        className={`grid h-6 w-6 shrink-0 place-items-center rounded-full ${
                          step.type === "tool_call" ? "bg-accent text-white" : step.type === "final_answer" ? "bg-ink-950 text-white" : "bg-mist-100 text-ink-700"
                        }`}
                      >
                        <Icon size={12} />
                      </span>
                      {i < trace.length - 1 && <span className="my-1 w-px flex-1 bg-mist-200" />}
                    </div>
                    <div className="min-w-0 flex-1 pb-3">
                      <p className="text-[12px] font-medium text-ink-950">{step.title || LABELS[step.type]}</p>
                      <div className="mt-1.5">
                        <StepDetail step={step} />
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

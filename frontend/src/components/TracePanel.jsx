import { useState } from "react";
import { FileText, Search, Wrench, MessageCircle, ChevronDown } from "lucide-react";

const ICONS = {
  system_prompt: FileText,
  retrieval: Search,
  tool_call: Wrench,
  final_answer: MessageCircle,
};

const LABELS = {
  system_prompt: "Prompt de sistema",
  retrieval: "Recuperación (RAG)",
  tool_call: "Llamada a herramienta",
  final_answer: "Respuesta final",
};

function StepDetail({ step }) {
  if (step.type === "retrieval") {
    return (
      <div className="space-y-1.5">
        {step.detail.map((d, i) => (
          <div key={i} className="rounded-lg bg-mist-50 px-2.5 py-1.5 text-[12px] text-ink-800">
            <span className="mr-2 tabular font-medium text-tcs-dark">{d.score}</span>
            {d.preview}…
          </div>
        ))}
      </div>
    );
  }
  if (step.type === "tool_call") {
    return (
      <div className="rounded-lg bg-mist-50 p-2.5 text-[12px]">
        <div className="mb-1 text-mist-500">Argumentos</div>
        <pre className="whitespace-pre-wrap break-words text-ink-800">{JSON.stringify(step.detail.argumentos, null, 2)}</pre>
        <div className="mb-1 mt-2 text-mist-500">Resultado</div>
        <pre className="whitespace-pre-wrap break-words text-ink-800">{JSON.stringify(step.detail.resultado, null, 2)}</pre>
      </div>
    );
  }
  return <p className="whitespace-pre-wrap text-[12.5px] text-ink-800">{String(step.detail)}</p>;
}

export default function TracePanel({ trace = [] }) {
  const [open, setOpen] = useState(false);
  if (!trace.length) return null;

  return (
    <div className="mt-2 rounded-xl border border-mist-200 bg-white">
      <button
        onClick={() => setOpen((v) => !v)}
        className="focus-ring flex w-full items-center justify-between rounded-xl px-3 py-2 text-left"
      >
        <span className="text-[11.5px] font-medium text-mist-500">
          Traza de ejecución · {trace.length} paso{trace.length !== 1 ? "s" : ""}
        </span>
        <ChevronDown size={14} className={`text-mist-400 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="space-y-3 border-t border-mist-100 px-3 py-3">
          {trace.map((step, i) => {
            const Icon = ICONS[step.type] || FileText;
            return (
              <div key={i} className="flex gap-2.5">
                <div className="flex flex-col items-center">
                  <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-tcs-50 text-tcs-dark">
                    <Icon size={12} />
                  </span>
                  {i < trace.length - 1 && <span className="mt-1 w-px flex-1 bg-mist-200" />}
                </div>
                <div className="flex-1 pb-1">
                  <p className="text-[11.5px] font-semibold text-ink-950">{step.title || LABELS[step.type]}</p>
                  <div className="mt-1">
                    <StepDetail step={step} />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

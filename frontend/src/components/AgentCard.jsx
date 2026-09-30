import { useNavigate } from "react-router-dom";
import { Cpu, Wrench } from "lucide-react";
import Badge from "./Badge";

export default function AgentCard({ agent }) {
  const navigate = useNavigate();
  return (
    <button
      onClick={() => navigate(`/agentes/${agent.id}`)}
      className="focus-ring group flex flex-col rounded-2xl border border-mist-200 bg-white p-5 text-left shadow-soft transition hover:-translate-y-0.5 hover:shadow-card"
    >
      <div className="flex items-start justify-between">
        <span className="grid h-11 w-11 place-items-center rounded-xl bg-mist-100 text-xl">
          {agent.avatar_emoji}
        </span>
        <Badge tone={agent.status === "active" ? "good" : "neutral"} dot>
          {agent.status === "active" ? "Activo" : "Inactivo"}
        </Badge>
      </div>
      <h3 className="mt-3.5 text-[15px] font-semibold text-ink-950 group-hover:text-tcs-dark">{agent.name}</h3>
      <p className="mt-1 line-clamp-2 text-[13px] text-mist-500">{agent.description}</p>
      <div className="mt-4 flex flex-wrap items-center gap-1.5 border-t border-mist-100 pt-3">
        <span className="inline-flex items-center gap-1 rounded-md bg-mist-50 px-2 py-1 text-[11px] text-mist-500">
          <Cpu size={11} /> {agent.model}
        </span>
        {agent.tools?.length > 0 && (
          <span className="inline-flex items-center gap-1 rounded-md bg-mist-50 px-2 py-1 text-[11px] text-mist-500">
            <Wrench size={11} /> {agent.tools.length} herramienta{agent.tools.length > 1 ? "s" : ""}
          </span>
        )}
      </div>
    </button>
  );
}

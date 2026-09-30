import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowUpRight, Cpu, Wrench } from "lucide-react";
import Badge from "./Badge";
import { AgentIcon } from "../lib/icons";
import { fmtCompact } from "../lib/format";

export default function AgentCard({ agent, usage, index = 0 }) {
  const navigate = useNavigate();
  const inactive = agent.status !== "active";
  return (
    <motion.button
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.04 }}
      onClick={() => navigate(`/agentes/${agent.id}`)}
      className="focus-ring group relative flex flex-col rounded-xl border border-mist-200 bg-white p-5 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-mist-300 hover:shadow-card"
    >
      <div className="flex items-start justify-between">
        <AgentIcon name={agent.icon} size="lg" tone={inactive ? "light" : "dark"} />
        <div className="flex items-center gap-2">
          {inactive ? <Badge>Pausado</Badge> : <Badge tone="good" dot>Activo</Badge>}
          <ArrowUpRight size={16} className="text-mist-300 transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-accent" />
        </div>
      </div>
      <h3 className="mt-4 text-[15px] font-semibold tracking-tight text-ink-950">{agent.name}</h3>
      <p className="mt-1 line-clamp-2 min-h-[38px] text-[13px] leading-relaxed text-mist-500">{agent.description}</p>
      <div className="mt-4 flex items-center gap-3 border-t border-mist-100 pt-3 text-[11.5px] text-mist-500">
        <span className="inline-flex items-center gap-1 font-mono">
          <Cpu size={12} /> {agent.model}
        </span>
        {agent.tools?.length > 0 && (
          <span className="inline-flex items-center gap-1">
            <Wrench size={12} /> {agent.tools.length}
          </span>
        )}
        {usage && (
          <span className="ml-auto font-medium tabular text-ink-700">{fmtCompact(usage.tokens)} tokens</span>
        )}
      </div>
    </motion.button>
  );
}

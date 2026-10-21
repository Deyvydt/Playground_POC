import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Plus, Bot, Search } from "lucide-react";
import PageHeader from "../components/PageHeader";
import AgentCard from "../components/AgentCard";
import EmptyState from "../components/EmptyState";
import AgentFormModal from "../components/AgentFormModal";
import { listAgents, createAgent, metricsSummary, errorMessage } from "../api/client";
import { useSession } from "../context/SessionContext";
import { useUI } from "../context/UIContext";

const FILTERS = [
  { id: "all", label: "Todos" },
  { id: "active", label: "Activos" },
  { id: "inactive", label: "Pausados" },
];

export default function Agents() {
  const [agents, setAgents] = useState([]);
  const [usage, setUsage] = useState({});
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const { can } = useSession();
  const { toast } = useUI();
  const showForm = params.get("nuevo") === "1" && can("create");

  const load = () => listAgents().then(setAgents).finally(() => setLoading(false));

  useEffect(() => {
    load();
    metricsSummary(30)
      .then((s) => setUsage(Object.fromEntries(s.agents_breakdown.map((a) => [a.agent_id, a]))))
      .catch(() => {});
  }, []);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return agents.filter(
      (a) =>
        (filter === "all" || a.status === filter) &&
        (!q || a.name.toLowerCase().includes(q) || (a.description || "").toLowerCase().includes(q))
    );
  }, [agents, query, filter]);

  const closeForm = () => setParams({});

  const handleCreate = async (payload) => {
    try {
      const agent = await createAgent(payload);
      toast(`Agente “${agent.name}” creado`);
      closeForm();
      navigate(`/agentes/${agent.id}`);
    } catch (err) {
      toast(errorMessage(err, "No se pudo crear el agente"), "error");
    }
  };

  return (
    <div>
      <PageHeader
        title="Agentes"
        description="Crea, prueba y administra los agentes de la organización"
        actions={
          can("create") && (
            <button onClick={() => setParams({ nuevo: "1" })} className="btn-primary">
              <Plus size={15} /> Nuevo agente
            </button>
          )
        }
      />
      <div className="mx-auto max-w-[1200px] px-8 py-8">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative w-full sm:w-80">
            <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-mist-400" />
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar agentes…" className="input pl-9" />
          </div>
          <div className="inline-flex rounded-lg border border-mist-200 bg-white p-0.5">
            {FILTERS.map((f) => (
              <button
                key={f.id}
                onClick={() => setFilter(f.id)}
                className={`focus-ring rounded-md px-3 py-1.5 text-[12.5px] font-medium transition ${
                  filter === f.id ? "bg-ink-950 text-white" : "text-mist-500 hover:text-ink-950"
                }`}
              >
                {f.label}
                <span className={`ml-1.5 tabular ${filter === f.id ? "text-white/60" : "text-mist-400"}`}>
                  {f.id === "all" ? agents.length : agents.filter((a) => a.status === f.id).length}
                </span>
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-[196px] animate-pulse rounded-xl bg-mist-100" />
            ))}
          </div>
        ) : visible.length === 0 ? (
          <EmptyState
            icon={Bot}
            title={agents.length ? "Sin coincidencias" : "Aún no hay agentes"}
            description={agents.length ? "Prueba con otro término o filtro." : "Crea el primer agente de tu organización."}
            action={
              !agents.length && can("create") && (
                <button onClick={() => setParams({ nuevo: "1" })} className="btn-primary">
                  <Plus size={15} /> Nuevo agente
                </button>
              )
            }
          />
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {visible.map((a, i) => (
              <AgentCard key={a.id} agent={a} usage={usage[a.id]} index={i} />
            ))}
          </div>
        )}
      </div>

      <AgentFormModal open={showForm} onSubmit={handleCreate} onClose={closeForm} />
    </div>
  );
}

import { useEffect, useState } from "react";
import { Plus, Bot } from "lucide-react";
import TopBar from "../components/TopBar";
import AgentCard from "../components/AgentCard";
import EmptyState from "../components/EmptyState";
import AgentFormModal from "../components/AgentFormModal";
import { listAgents, createAgent } from "../api/client";
import { useSession } from "../context/SessionContext";

export default function Agents() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const { can } = useSession();

  const load = () => listAgents().then(setAgents).finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  const handleCreate = async (payload) => {
    await createAgent(payload);
    setShowForm(false);
    load();
  };

  return (
    <div>
      <TopBar title="Agentes" description="Crea, configura y administra los agentes de IA de la organización" />
      <div className="mx-auto max-w-6xl px-8 py-8">
        <div className="mb-5 flex items-center justify-between">
          <p className="text-[13px] text-mist-500">{agents.length} agente{agents.length !== 1 ? "s" : ""} registrado{agents.length !== 1 ? "s" : ""}</p>
          {can("create") && (
            <button
              onClick={() => setShowForm(true)}
              className="focus-ring inline-flex items-center gap-2 rounded-xl bg-ink-950 px-4 py-2.5 text-[13px] font-semibold text-white hover:bg-ink-800"
            >
              <Plus size={15} /> Nuevo agente
            </button>
          )}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-40 animate-pulse rounded-2xl bg-mist-100" />
            ))}
          </div>
        ) : agents.length === 0 ? (
          <EmptyState icon={Bot} title="Aún no hay agentes" description="Crea tu primer agente para comenzar a probarlo en el playground." />
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {agents.map((a) => (
              <AgentCard key={a.id} agent={a} />
            ))}
          </div>
        )}
      </div>

      {showForm && <AgentFormModal onSubmit={handleCreate} onClose={() => setShowForm(false)} />}
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft, Send, Upload, FileText, Trash2, Pencil, Cpu, Thermometer, Wrench, Gauge, MessagesSquare, Timer,
} from "lucide-react";
import Badge from "../components/Badge";
import ChatBubble from "../components/ChatBubble";
import TypingDots from "../components/TypingDots";
import EmptyState from "../components/EmptyState";
import AgentFormModal from "../components/AgentFormModal";
import StatTile from "../components/StatTile";
import { useSession } from "../context/SessionContext";
import {
  getAgent, updateAgent, deleteAgent, listKnowledge, uploadKnowledge, deleteKnowledge,
  sendMessage, metricsSummary,
} from "../api/client";

const TABS = [
  { id: "playground", label: "Playground" },
  { id: "config", label: "Configuración" },
  { id: "knowledge", label: "Conocimiento" },
  { id: "metrics", label: "Métricas" },
];

function PlaygroundTab({ agent }) {
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const send = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setSending(true);
    try {
      const res = await sendMessage(agent.id, { message: text, conversation_id: conversationId });
      setConversationId(res.conversation_id);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.message.content, trace: res.trace, latencyMs: res.latency_ms },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "⚠️ No se pudo contactar al modelo. Verifica que Ollama esté activo." },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-15rem)] flex-col rounded-2xl border border-mist-200 bg-white">
      <div className="flex-1 space-y-4 overflow-y-auto p-5 scrollbar-thin">
        {messages.length === 0 && (
          <EmptyState
            icon={MessagesSquare}
            title="Empieza una conversación"
            description={`Prueba a ${agent.name} en tiempo real. Cada respuesta muestra su traza de razonamiento paso a paso.`}
          />
        )}
        {messages.map((m, i) => (
          <ChatBubble key={i} role={m.role} content={m.content} trace={m.trace} latencyMs={m.latencyMs} agentEmoji={agent.avatar_emoji} />
        ))}
        {sending && (
          <div className="flex gap-2.5">
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-mist-100 text-[15px]">{agent.avatar_emoji}</span>
            <div className="rounded-2xl border border-mist-200 bg-white px-2"><TypingDots /></div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={send} className="flex items-center gap-2 border-t border-mist-100 p-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`Escribe un mensaje para ${agent.name}...`}
          className="focus-ring flex-1 rounded-xl border border-mist-200 px-3.5 py-2.5 text-[13.5px]"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="focus-ring grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-ink-950 text-white hover:bg-ink-800 disabled:opacity-40"
        >
          <Send size={15} />
        </button>
      </form>
    </div>
  );
}

function ConfigTab({ agent }) {
  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-mist-200 bg-white p-5">
        <h3 className="mb-3 text-[12px] font-semibold uppercase tracking-wide text-mist-400">Prompt de sistema</h3>
        <p className="whitespace-pre-wrap text-[13.5px] leading-relaxed text-ink-800">{agent.role_prompt}</p>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-mist-200 bg-white p-4">
          <div className="flex items-center gap-2 text-mist-500"><Cpu size={14} /><span className="text-[12px] font-medium">Modelo</span></div>
          <p className="mt-1.5 text-[14px] font-semibold text-ink-950">{agent.model}</p>
        </div>
        <div className="rounded-2xl border border-mist-200 bg-white p-4">
          <div className="flex items-center gap-2 text-mist-500"><Thermometer size={14} /><span className="text-[12px] font-medium">Temperatura</span></div>
          <p className="mt-1.5 text-[14px] font-semibold text-ink-950">{agent.temperature}</p>
        </div>
        <div className="rounded-2xl border border-mist-200 bg-white p-4">
          <div className="flex items-center gap-2 text-mist-500"><Wrench size={14} /><span className="text-[12px] font-medium">Herramientas</span></div>
          <p className="mt-1.5 text-[14px] font-semibold text-ink-950">{agent.tools?.length || 0} activa(s)</p>
        </div>
      </div>
      {agent.tools?.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {agent.tools.map((t) => <Badge key={t} tone="tcs">{t}</Badge>)}
        </div>
      )}
    </div>
  );
}

function KnowledgeTab({ agent }) {
  const [docs, setDocs] = useState([]);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef(null);

  const load = () => listKnowledge(agent.id).then(setDocs);
  useEffect(() => { load(); }, [agent.id]);

  const handleFile = async (file) => {
    if (!file) return;
    setUploading(true);
    try {
      await uploadKnowledge(agent.id, file);
      await load();
    } catch {
      alert("No se pudo procesar el documento. Verifica que Ollama esté activo (modelo de embeddings).");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); handleFile(e.dataTransfer.files?.[0]); }}
        className="rounded-2xl border-2 border-dashed border-mist-300 bg-white p-8 text-center"
      >
        <Upload size={20} className="mx-auto text-mist-400" />
        <p className="mt-2 text-[13px] font-medium text-ink-950">
          Arrastra un archivo .txt o .pdf, o
          <button onClick={() => fileRef.current?.click()} className="focus-ring ml-1 text-tcs-dark underline">
            selecciona uno
          </button>
        </p>
        <p className="mt-1 text-[11.5px] text-mist-400">
          Se fragmenta y se indexa con embeddings locales (nomic-embed-text) para responder con RAG.
        </p>
        <input ref={fileRef} type="file" accept=".txt,.md,.pdf" hidden onChange={(e) => handleFile(e.target.files?.[0])} />
        {uploading && <p className="mt-2 text-[12px] text-tcs-dark">Procesando documento…</p>}
      </div>

      {docs.length === 0 ? (
        <EmptyState icon={FileText} title="Sin documentos" description="Esta base de conocimiento aún no tiene archivos." />
      ) : (
        <div className="divide-y divide-mist-100 rounded-2xl border border-mist-200 bg-white">
          {docs.map((d) => (
            <div key={d.id} className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center gap-3">
                <span className="grid h-9 w-9 place-items-center rounded-lg bg-mist-100"><FileText size={15} className="text-mist-500" /></span>
                <div>
                  <p className="text-[13px] font-medium text-ink-950">{d.filename}</p>
                  <p className="text-[11.5px] text-mist-500">{d.chunk_count} fragmentos indexados</p>
                </div>
              </div>
              <button
                onClick={async () => { await deleteKnowledge(d.id); load(); }}
                className="focus-ring rounded-lg p-2 text-mist-400 hover:bg-red-50 hover:text-red-600"
              >
                <Trash2 size={15} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MetricsTab({ agent }) {
  const [row, setRow] = useState(null);
  useEffect(() => {
    metricsSummary().then((s) => setRow(s.agents_breakdown.find((a) => a.agent_id === agent.id) || null));
  }, [agent.id]);

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <StatTile label="Solicitudes" value={row?.requests ?? 0} icon={MessagesSquare} />
      <StatTile label="Tokens totales" value={row?.tokens ?? 0} icon={Gauge} />
      <StatTile label="Latencia promedio" value={row ? `${row.avg_latency_ms} ms` : "0 ms"} icon={Timer} />
    </div>
  );
}

export default function AgentDetail() {
  const { agentId } = useParams();
  const navigate = useNavigate();
  const { can } = useSession();
  const [agent, setAgent] = useState(null);
  const [tab, setTab] = useState("playground");
  const [editing, setEditing] = useState(false);

  const load = () => getAgent(agentId).then(setAgent);
  useEffect(() => { load(); }, [agentId]);

  if (!agent) return <div className="p-8 text-[13px] text-mist-500">Cargando agente…</div>;

  const handleUpdate = async (payload) => {
    await updateAgent(agent.id, payload);
    setEditing(false);
    load();
  };

  const handleDelete = async () => {
    if (!confirm(`¿Eliminar el agente "${agent.name}"? Esta acción no se puede deshacer.`)) return;
    await deleteAgent(agent.id);
    navigate("/agentes");
  };

  return (
    <div className="mx-auto max-w-5xl px-8 py-6">
      <button onClick={() => navigate("/agentes")} className="focus-ring mb-4 inline-flex items-center gap-1.5 text-[12.5px] font-medium text-mist-500 hover:text-ink-950">
        <ArrowLeft size={14} /> Volver a agentes
      </button>

      <div className="mb-6 flex items-start justify-between">
        <div className="flex items-center gap-3.5">
          <span className="grid h-14 w-14 place-items-center rounded-2xl bg-mist-100 text-2xl">{agent.avatar_emoji}</span>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-[19px] font-semibold text-ink-950">{agent.name}</h1>
              <Badge tone={agent.status === "active" ? "good" : "neutral"} dot>{agent.status === "active" ? "Activo" : "Inactivo"}</Badge>
            </div>
            <p className="text-[13px] text-mist-500">{agent.description}</p>
          </div>
        </div>
        {can("create") && (
          <div className="flex gap-2">
            <button onClick={() => setEditing(true)} className="focus-ring inline-flex items-center gap-1.5 rounded-xl border border-mist-200 bg-white px-3.5 py-2 text-[12.5px] font-medium text-ink-950 hover:bg-mist-50">
              <Pencil size={13} /> Editar
            </button>
            {can("delete") && (
              <button onClick={handleDelete} className="focus-ring inline-flex items-center gap-1.5 rounded-xl border border-mist-200 bg-white px-3.5 py-2 text-[12.5px] font-medium text-red-600 hover:bg-red-50">
                <Trash2 size={13} /> Eliminar
              </button>
            )}
          </div>
        )}
      </div>

      <div className="mb-5 flex gap-1 border-b border-mist-200">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`focus-ring -mb-px border-b-2 px-3.5 py-2.5 text-[13px] font-medium transition ${
              tab === t.id ? "border-ink-950 text-ink-950" : "border-transparent text-mist-500 hover:text-ink-950"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "playground" && <PlaygroundTab agent={agent} />}
      {tab === "config" && <ConfigTab agent={agent} />}
      {tab === "knowledge" && <KnowledgeTab agent={agent} />}
      {tab === "metrics" && <MetricsTab agent={agent} />}

      {editing && <AgentFormModal initial={agent} onSubmit={handleUpdate} onClose={() => setEditing(false)} />}
    </div>
  );
}

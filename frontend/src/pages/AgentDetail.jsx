import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip as RTooltip, XAxis, YAxis } from "recharts";
import {
  ArrowUp, Upload, FileText, Trash2, Pencil, Cpu, Thermometer, Wrench, Coins, MessagesSquare, Timer,
  Plus, MessageSquare, Pause, Play, Loader2, CircleAlert, User, CalendarDays,
} from "lucide-react";
import PageHeader from "../components/PageHeader";
import Badge from "../components/Badge";
import ChatBubble from "../components/ChatBubble";
import TypingDots from "../components/TypingDots";
import EmptyState from "../components/EmptyState";
import AgentFormModal from "../components/AgentFormModal";
import StatTile from "../components/StatTile";
import Tooltip from "../components/Tooltip";
import ChartTooltip, { AXIS, GRID } from "../components/ChartTooltip";
import { AgentIcon } from "../lib/icons";
import { useSession } from "../context/SessionContext";
import { useUI } from "../context/UIContext";
import { fmtCompact, fmtDay, fmtLatency, fmtNumber, fmtPct, fmtRelative, parseDate } from "../lib/format";
import {
  getAgent, updateAgent, deleteAgent, listKnowledge, uploadKnowledge, deleteKnowledge, sendMessage,
  metricsSummary, metricsTimeseries, listConversations, listMessages, deleteConversation, listTools, errorMessage,
} from "../api/client";

const TABS = [
  { id: "chat", label: "Conversación" },
  { id: "config", label: "Configuración" },
  { id: "knowledge", label: "Conocimiento" },
  { id: "metrics", label: "Métricas" },
];

const SUGGESTIONS = {
  "Soporte TI": ["¿Cuál es el estado del ticket TCS-4471?", "Mi VPN no conecta desde casa, ¿qué reviso primero?", "¿Qué día y hora es hoy?"],
  "Analista de Datos": ["Si vendimos 1,250,000 con un margen de 18%, ¿cuál fue la utilidad?", "Las ventas pasaron de 820K a 910K. ¿Cuál fue el crecimiento?"],
  "Redactor de Reportes": ["Resume para gerencia: el proyecto va 2 semanas atrasado por falta de accesos del cliente."],
  "Asesor de Onboarding": ["¿Cuántos días de vacaciones acumulo por mes?", "¿Qué capacitaciones son obligatorias al ingresar?", "¿Cuál es el horario de trabajo?"],
  "Asistente de RR.HH.": ["¿Cómo solicito un permiso por motivos personales?", "¿Qué beneficios tengo como nuevo colaborador?"],
};
const DEFAULT_SUGGESTIONS = ["¿Qué puedes hacer por mí?", "Explícame tu función en tres puntos."];

function ChatTab({ agent }) {
  const [conversations, setConversations] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const { confirm } = useUI();
  const paused = agent.status !== "active";

  const loadConversations = () => listConversations(agent.id).then(setConversations).catch(() => {});
  useEffect(() => {
    loadConversations();
  }, [agent.id]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, sending]);

  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [input]);

  const openConversation = async (id) => {
    setConversationId(id);
    setLoadingHistory(true);
    try {
      setMessages(await listMessages(id));
    } finally {
      setLoadingHistory(false);
    }
  };

  const newConversation = () => {
    setConversationId(null);
    setMessages([]);
    inputRef.current?.focus();
  };

  const removeConversation = async (id) => {
    const ok = await confirm({ title: "¿Eliminar conversación?", description: "Se borrará todo su historial.", confirmLabel: "Eliminar", danger: true });
    if (!ok) return;
    await deleteConversation(id);
    if (id === conversationId) newConversation();
    loadConversations();
  };

  const send = async (text) => {
    const content = (text ?? input).trim();
    if (!content || sending || paused) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content }]);
    setSending(true);
    try {
      const res = await sendMessage(agent.id, { message: content, conversation_id: conversationId });
      if (!conversationId) loadConversations();
      setConversationId(res.conversation_id);
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: res.message.content,
          trace: res.trace,
          latency_ms: res.latency_ms,
          prompt_tokens: res.prompt_tokens,
          completion_tokens: res.completion_tokens,
        },
      ]);
    } catch (err) {
      if (!conversationId) loadConversations();
      setMessages((m) => [
        ...m,
        { role: "assistant", error: true, content: errorMessage(err, "No se pudo obtener una respuesta. Intenta nuevamente.") },
      ]);
    } finally {
      setSending(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const suggestions = SUGGESTIONS[agent.name] || DEFAULT_SUGGESTIONS;

  return (
    <div className="flex h-[calc(100vh-15.5rem)] min-h-[480px] overflow-hidden rounded-xl border border-mist-200 bg-white">
      <aside className="hidden w-60 shrink-0 flex-col border-r border-mist-100 bg-mist-50/50 md:flex">
        <div className="p-3">
          <button onClick={newConversation} className="btn-secondary w-full justify-start">
            <Plus size={14} /> Nueva conversación
          </button>
        </div>
        <p className="eyebrow px-4 pb-1">Historial</p>
        <div className="flex-1 space-y-0.5 overflow-y-auto px-2 pb-3">
          {conversations.length === 0 && <p className="px-2 py-3 text-[12px] text-mist-400">Tus conversaciones aparecerán aquí.</p>}
          {conversations.map((c) => (
            <div
              key={c.id}
              className={`group flex items-center rounded-lg transition ${c.id === conversationId ? "bg-white shadow-soft ring-1 ring-mist-200" : "hover:bg-white"}`}
            >
              <button onClick={() => openConversation(c.id)} className="focus-ring min-w-0 flex-1 px-2.5 py-2 text-left">
                <span className="block truncate text-[12.5px] text-ink-950">{c.title}</span>
                <span className="block text-[11px] text-mist-400">{fmtRelative(c.started_at)}</span>
              </button>
              <Tooltip label="Eliminar conversación">
                <button onClick={() => removeConversation(c.id)} className="btn-icon mr-1 h-7 w-7 opacity-0 group-hover:opacity-100">
                  <Trash2 size={13} />
                </button>
              </Tooltip>
            </div>
          ))}
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-3xl space-y-6 px-6 py-6">
            {loadingHistory && (
              <div className="flex justify-center py-10 text-mist-400">
                <Loader2 size={18} className="animate-spin" />
              </div>
            )}
            {!loadingHistory && messages.length === 0 && (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col items-center pt-10 text-center">
                <AgentIcon name={agent.icon} size="xl" tone="dark" />
                <h3 className="mt-4 font-serif text-[28px] leading-tight text-ink-950">¿En qué te ayudo hoy?</h3>
                <p className="mt-1 max-w-md text-[13.5px] text-mist-500">{agent.description}</p>
                {!paused && (
                  <div className="mt-7 grid w-full max-w-xl gap-2">
                    {suggestions.map((s, i) => (
                      <motion.button
                        key={s}
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 + i * 0.05 }}
                        onClick={() => send(s)}
                        className="focus-ring group flex items-center justify-between rounded-xl border border-mist-200 px-4 py-3 text-left text-[13.5px] text-ink-800 transition hover:border-accent hover:bg-accent-50/40"
                      >
                        {s}
                        <ArrowUp size={14} className="rotate-45 text-mist-300 transition group-hover:text-accent" />
                      </motion.button>
                    ))}
                  </div>
                )}
              </motion.div>
            )}
            {messages.map((m, i) => (
              <ChatBubble key={i} message={m} agentIcon={agent.icon} />
            ))}
            {sending && (
              <div className="flex gap-3">
                <AgentIcon name={agent.icon} size="sm" tone="dark" />
                <TypingDots />
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        <div className="border-t border-mist-100 p-4">
          {paused ? (
            <p className="flex items-center justify-center gap-2 rounded-xl bg-mist-50 py-3 text-[13px] text-mist-500">
              <Pause size={14} /> Este agente está pausado. Actívalo para conversar.
            </p>
          ) : (
            <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-mist-200 bg-white p-2 shadow-soft transition focus-within:border-accent focus-within:shadow-glow">
              <textarea
                ref={inputRef}
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder={`Escribe a ${agent.name}…`}
                className="max-h-40 flex-1 resize-none bg-transparent px-2 py-1.5 text-[14px] text-ink-950 placeholder:text-mist-400 focus:outline-none"
              />
              <Tooltip label="Enviar" shortcut="Enter">
                <button
                  onClick={() => send()}
                  disabled={sending || !input.trim()}
                  className="btn h-9 w-9 shrink-0 rounded-xl bg-accent text-white hover:bg-accent-dark"
                >
                  <ArrowUp size={16} strokeWidth={2.25} />
                </button>
              </Tooltip>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ConfigTab({ agent }) {
  const [tools, setTools] = useState([]);
  useEffect(() => {
    listTools().then(setTools).catch(() => {});
  }, []);
  const toolInfo = Object.fromEntries(tools.map((t) => [t.name, t.description]));

  const params = [
    { icon: Cpu, label: "Modelo", value: <span className="font-mono">{agent.model}</span> },
    { icon: Thermometer, label: "Temperatura", value: Number(agent.temperature).toFixed(1) },
    { icon: User, label: "Creado por", value: agent.created_by },
    { icon: CalendarDays, label: "Creado", value: parseDate(agent.created_at)?.toLocaleDateString("es-PE", { day: "numeric", month: "short", year: "numeric" }) },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <div className="card p-5 lg:col-span-2">
        <p className="eyebrow">Instrucciones del sistema</p>
        <p className="mt-3 whitespace-pre-wrap text-[14px] leading-relaxed text-ink-800">{agent.role_prompt}</p>
      </div>
      <div className="space-y-4">
        <div className="card divide-y divide-mist-100">
          {params.map((p) => (
            <div key={p.label} className="flex items-center justify-between px-4 py-3">
              <span className="flex items-center gap-2 text-[12.5px] text-mist-500">
                <p.icon size={14} /> {p.label}
              </span>
              <span className="text-[13px] font-medium text-ink-950">{p.value}</span>
            </div>
          ))}
        </div>
        <div className="card p-4">
          <p className="eyebrow flex items-center gap-1.5">
            <Wrench size={12} /> Herramientas
          </p>
          {agent.tools?.length ? (
            <ul className="mt-3 space-y-2.5">
              {agent.tools.map((t) => (
                <li key={t}>
                  <p className="font-mono text-[12.5px] text-ink-950">{t}</p>
                  {toolInfo[t] && <p className="text-[12px] text-mist-500">{toolInfo[t]}</p>}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-[12.5px] text-mist-500">Sin herramientas habilitadas.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function KnowledgeTab({ agent }) {
  const [docs, setDocs] = useState([]);
  const [uploading, setUploading] = useState(null);
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef(null);
  const { can } = useSession();
  const { toast, confirm } = useUI();
  const editable = can("knowledge");

  const load = () => listKnowledge(agent.id).then(setDocs).catch(() => {});
  useEffect(() => {
    load();
  }, [agent.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleFile = async (file) => {
    if (!file) return;
    setUploading(file.name);
    try {
      const doc = await uploadKnowledge(agent.id, file);
      toast(`“${doc.filename}” indexado en ${doc.chunk_count} fragmentos`);
      await load();
    } catch (err) {
      toast(errorMessage(err, "No se pudo procesar el documento"), "error");
    } finally {
      setUploading(null);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const remove = async (doc) => {
    const ok = await confirm({
      title: `¿Quitar “${doc.filename}”?`,
      description: "El agente dejará de usar este documento para responder.",
      confirmLabel: "Quitar",
      danger: true,
    });
    if (!ok) return;
    await deleteKnowledge(doc.id);
    toast("Documento eliminado");
    load();
  };

  return (
    <div className="space-y-4">
      {editable && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            handleFile(e.dataTransfer.files?.[0]);
          }}
          onClick={() => !uploading && fileRef.current?.click()}
          className={`cursor-pointer rounded-xl border-2 border-dashed p-10 text-center transition ${
            dragging ? "border-accent bg-accent-50" : "border-mist-300 bg-white hover:border-mist-400"
          }`}
        >
          {uploading ? (
            <div className="flex flex-col items-center gap-2 text-[13px] text-ink-800">
              <Loader2 size={22} className="animate-spin text-accent" />
              Indexando “{uploading}”…
            </div>
          ) : (
            <>
              <span className="mx-auto grid h-11 w-11 place-items-center rounded-xl bg-mist-100 text-ink-700">
                <Upload size={18} />
              </span>
              <p className="mt-3 text-[14px] font-medium text-ink-950">Arrastra un documento o haz clic para seleccionarlo</p>
              <p className="mt-1 text-[12.5px] text-mist-500">PDF, TXT o MD · hasta 10 MB</p>
            </>
          )}
          <input ref={fileRef} type="file" accept=".txt,.md,.pdf" hidden onChange={(e) => handleFile(e.target.files?.[0])} />
        </div>
      )}

      {docs.length === 0 ? (
        <EmptyState icon={FileText} title="Sin documentos" description="Agrega documentos para que el agente responda con información de la organización." compact />
      ) : (
        <div className="card divide-y divide-mist-100">
          {docs.map((d) => (
            <div key={d.id} className="flex items-center gap-3 px-4 py-3">
              <span className="grid h-9 w-9 place-items-center rounded-lg bg-mist-100 text-ink-700">
                <FileText size={16} />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13.5px] font-medium text-ink-950">{d.filename}</p>
                <p className="text-[12px] text-mist-500">
                  {d.chunk_count} fragmentos · {fmtRelative(d.uploaded_at)}
                </p>
              </div>
              {editable && (
                <Tooltip label="Quitar documento">
                  <button onClick={() => remove(d)} className="btn-icon hover:bg-red-50 hover:text-red-600">
                    <Trash2 size={15} />
                  </button>
                </Tooltip>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MetricsTab({ agent }) {
  const [row, setRow] = useState(null);
  const [series, setSeries] = useState([]);
  useEffect(() => {
    metricsSummary(30).then((s) => setRow(s.agents_breakdown.find((a) => a.agent_id === agent.id) || { requests: 0, tokens: 0, avg_latency_ms: 0, errors: 0 }));
    metricsTimeseries(30, agent.id).then(setSeries).catch(() => {});
  }, [agent.id]);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Tokens (30 días)" icon={Coins} value={row?.tokens} format={fmtCompact} highlight />
        <StatTile label="Solicitudes" icon={MessagesSquare} value={row?.requests} format={fmtNumber} delay={0.05} />
        <StatTile label="Latencia promedio" icon={Timer} value={row ? fmtLatency(row.avg_latency_ms) : null} delay={0.1} />
        <StatTile label="Errores" icon={CircleAlert} value={row ? fmtPct(row.requests ? row.errors / row.requests : 0) : null} delay={0.15}
          sub={row && `${row.errors} de ${row.requests}`} />
      </div>
      <div className="card p-5">
        <div className="flex items-baseline justify-between">
          <h4 className="text-[13.5px] font-semibold text-ink-950">Tokens por día</h4>
          <div className="flex items-center gap-4 text-[12px] text-mist-500">
            <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-accent" /> Entrada</span>
            <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-ink-950" /> Salida</span>
          </div>
        </div>
        <div className="mt-4 h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={series} margin={{ left: -8, right: 4, top: 6 }}>
              <CartesianGrid vertical={false} stroke={GRID} />
              <XAxis dataKey="date" tickFormatter={fmtDay} tick={AXIS} axisLine={false} tickLine={false} minTickGap={28} />
              <YAxis tickFormatter={fmtCompact} tick={AXIS} axisLine={false} tickLine={false} width={44} />
              <RTooltip content={<ChartTooltip />} cursor={{ stroke: "#D9D6CD" }} />
              <Area type="monotone" stackId="1" dataKey="prompt_tokens" name="Entrada" stroke="#E3622E" fill="#E3622E" fillOpacity={0.18} strokeWidth={2} />
              <Area type="monotone" stackId="1" dataKey="completion_tokens" name="Salida" stroke="#141413" fill="#141413" fillOpacity={0.08} strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

export default function AgentDetail() {
  const { agentId } = useParams();
  const navigate = useNavigate();
  const { can } = useSession();
  const { toast, confirm } = useUI();
  const [agent, setAgent] = useState(null);
  const [tab, setTab] = useState("chat");
  const [editing, setEditing] = useState(false);
  const [notFound, setNotFound] = useState(false);

  const load = () =>
    getAgent(agentId)
      .then(setAgent)
      .catch(() => setNotFound(true));
  useEffect(() => {
    setAgent(null);
    setTab("chat");
    load();
  }, [agentId]); // eslint-disable-line react-hooks/exhaustive-deps

  if (notFound)
    return (
      <div className="p-8">
        <EmptyState icon={CircleAlert} title="Agente no encontrado" action={<button className="btn-secondary" onClick={() => navigate("/agentes")}>Volver a agentes</button>} />
      </div>
    );
  if (!agent)
    return (
      <div className="flex h-screen items-center justify-center text-mist-400">
        <Loader2 className="animate-spin" size={20} />
      </div>
    );

  const handleUpdate = async (payload) => {
    try {
      setAgent(await updateAgent(agent.id, payload));
      setEditing(false);
      toast("Cambios guardados");
    } catch (err) {
      toast(errorMessage(err, "No se pudieron guardar los cambios"), "error");
    }
  };

  const toggleStatus = async () => {
    const status = agent.status === "active" ? "inactive" : "active";
    setAgent(await updateAgent(agent.id, { status }));
    toast(status === "active" ? "Agente activado" : "Agente pausado", "info");
  };

  const handleDelete = async () => {
    const ok = await confirm({
      title: `¿Eliminar “${agent.name}”?`,
      description: "Se eliminarán sus conversaciones y documentos. El historial de consumo se conserva.",
      confirmLabel: "Eliminar agente",
      danger: true,
    });
    if (!ok) return;
    await deleteAgent(agent.id);
    toast("Agente eliminado");
    navigate("/agentes");
  };

  const active = agent.status === "active";

  return (
    <div>
      <PageHeader
        eyebrow={
          <button onClick={() => navigate("/agentes")} className="hover:text-ink-950">
            Agentes
          </button>
        }
        title={agent.name}
        actions={
          can("edit") && (
            <div className="flex items-center gap-1">
              <Tooltip label={active ? "Pausar agente" : "Activar agente"} side="bottom">
                <button onClick={toggleStatus} className="btn-icon h-9 w-9">
                  {active ? <Pause size={16} /> : <Play size={16} />}
                </button>
              </Tooltip>
              {can("delete") && (
                <Tooltip label="Eliminar agente" side="bottom">
                  <button onClick={handleDelete} className="btn-icon h-9 w-9 hover:bg-red-50 hover:text-red-600">
                    <Trash2 size={16} />
                  </button>
                </Tooltip>
              )}
              <button onClick={() => setEditing(true)} className="btn-secondary ml-1">
                <Pencil size={14} /> Editar
              </button>
            </div>
          )
        }
      />

      <div className="mx-auto max-w-[1200px] px-8 pt-6">
        <div className="flex items-center gap-4">
          <AgentIcon name={agent.icon} size="xl" tone={active ? "dark" : "light"} />
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h2 className="text-[20px] font-semibold tracking-tight text-ink-950">{agent.name}</h2>
              {active ? <Badge tone="good" dot>Activo</Badge> : <Badge>Pausado</Badge>}
            </div>
            <p className="mt-0.5 truncate text-[13.5px] text-mist-500">{agent.description}</p>
          </div>
        </div>

        <div className="relative mt-5 flex gap-1 border-b border-mist-200">
          {TABS.filter((t) => t.id !== "metrics" || can("metrics")).map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`focus-ring relative px-3 py-2.5 text-[13.5px] font-medium transition ${tab === t.id ? "text-ink-950" : "text-mist-500 hover:text-ink-950"}`}
            >
              {t.label}
              {tab === t.id && <motion.span layoutId="agent-tab" className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-accent" />}
            </button>
          ))}
        </div>
      </div>

      <div className="mx-auto max-w-[1200px] px-8 py-5">
        <AnimatePresence mode="wait">
          <motion.div key={tab} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.18 }}>
            {tab === "chat" && <ChatTab agent={agent} />}
            {tab === "config" && <ConfigTab agent={agent} />}
            {tab === "knowledge" && <KnowledgeTab agent={agent} />}
            {tab === "metrics" && <MetricsTab agent={agent} />}
          </motion.div>
        </AnimatePresence>
      </div>

      <AgentFormModal open={editing} initial={agent} onSubmit={handleUpdate} onClose={() => setEditing(false)} />
    </div>
  );
}

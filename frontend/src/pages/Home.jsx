import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip as RTooltip, XAxis, YAxis } from "recharts";
import { ArrowRight, Coins, Gauge, MessagesSquare, Plus, Timer, Workflow, CircleAlert, Sparkles } from "lucide-react";
import PageHeader from "../components/PageHeader";
import StatTile from "../components/StatTile";
import AgentCard from "../components/AgentCard";
import ChartTooltip, { AXIS, GRID } from "../components/ChartTooltip";
import { AgentIcon } from "../lib/icons";
import { listAgents, metricsActivity, metricsSummary, metricsTimeseries } from "../api/client";
import { useSession } from "../context/SessionContext";
import { fmtCompact, fmtDay, fmtLatency, fmtNumber, fmtRelative, fmtUSD, greeting } from "../lib/format";

function QuickAction({ icon: Icon, title, desc, onClick, delay }) {
  return (
    <motion.button
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      onClick={onClick}
      className="focus-ring group flex items-center gap-3 rounded-xl border border-mist-200 bg-white px-4 py-3 text-left transition hover:border-mist-300 hover:shadow-card"
    >
      <span className="grid h-9 w-9 place-items-center rounded-lg bg-mist-100 text-ink-950 transition group-hover:bg-accent group-hover:text-white">
        <Icon size={16} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-[13.5px] font-medium text-ink-950">{title}</span>
        <span className="block truncate text-[12px] text-mist-500">{desc}</span>
      </span>
      <ArrowRight size={15} className="text-mist-300 transition group-hover:translate-x-0.5 group-hover:text-ink-950" />
    </motion.button>
  );
}

export default function Home() {
  const navigate = useNavigate();
  const { currentUser, can } = useSession();
  const [agents, setAgents] = useState([]);
  const [summary, setSummary] = useState(null);
  const [series, setSeries] = useState([]);
  const [activity, setActivity] = useState([]);
  const showMetrics = can("metrics");

  useEffect(() => {
    listAgents().then(setAgents).catch(() => {});
    if (showMetrics) {
      metricsSummary(30).then(setSummary).catch(() => {});
      metricsTimeseries(14).then(setSeries).catch(() => {});
      metricsActivity(7).then(setActivity).catch(() => {});
    }
  }, [showMetrics]);

  const agentById = useMemo(() => Object.fromEntries(agents.map((a) => [a.id, a])), [agents]);
  const topAgents = (summary?.agents_breakdown || []).slice(0, 5);
  const maxTokens = Math.max(1, ...topAgents.map((a) => a.tokens));
  const todayRaw = new Date().toLocaleDateString("es-PE", { weekday: "long", day: "numeric", month: "long" });
  const today = todayRaw.charAt(0).toUpperCase() + todayRaw.slice(1);

  return (
    <div>
      <PageHeader title="Inicio" description="Tu espacio de agentes" />
      <div className="mx-auto max-w-[1200px] px-8 pb-16 pt-10">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <p className="text-[13px] text-mist-500">{today}</p>
          <h2 className="mt-1 font-serif text-[40px] leading-tight tracking-tight text-ink-950">
            {greeting()}, <span className="italic text-accent">{currentUser?.name.split(" ")[0]}</span>
          </h2>
        </motion.div>

        <div className="mt-8 grid grid-cols-1 gap-3 md:grid-cols-3">
          {can("create") && (
            <QuickAction icon={Plus} title="Crear agente" desc="Define rol, modelo y herramientas" onClick={() => navigate("/agentes?nuevo=1")} delay={0.05} />
          )}
          <QuickAction
            icon={Sparkles}
            title="Probar un agente"
            desc="Conversa y revisa su razonamiento"
            onClick={() => navigate(agents[0] ? `/agentes/${agents.find((a) => a.status === "active")?.id || agents[0].id}` : "/agentes")}
            delay={0.1}
          />
          <QuickAction icon={Workflow} title="Ejecutar un flujo" desc="Encadena varios agentes" onClick={() => navigate("/flujos")} delay={0.15} />
        </div>

        {showMetrics ? (
          <>
            <div className="mt-10 flex items-end justify-between">
              <h3 className="text-[15px] font-semibold text-ink-950">Últimos 30 días</h3>
              <button onClick={() => navigate("/consumo")} className="btn-ghost text-[12.5px]">
                Ver consumo detallado <ArrowRight size={13} />
              </button>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-3 lg:grid-cols-4">
              <StatTile label="Tokens consumidos" icon={Coins} value={summary?.total_tokens} format={fmtCompact} highlight delay={0}
                sub={summary && `${fmtCompact(summary.prompt_tokens)} entrada · ${fmtCompact(summary.completion_tokens)} salida`} />
              <StatTile label="Solicitudes" icon={MessagesSquare} value={summary?.total_requests} format={fmtNumber} delay={0.05}
                sub={summary && `${summary.active_agents} agentes activos`} />
              <StatTile label="Latencia promedio" icon={Timer} value={summary ? fmtLatency(summary.avg_latency_ms) : null} delay={0.1}
                sub={summary && `${((1 - summary.error_rate) * 100).toFixed(1)}% de éxito`} />
              <StatTile label="Costo evitado" icon={Gauge} value={summary?.estimated_cloud_cost_usd} format={fmtUSD} delay={0.15}
                hint={summary && `Estimado a ${fmtUSD(summary.cloud_price_per_1k)} por 1K tokens en un proveedor en la nube`}
                sub="vs. proveedor en la nube" />
            </div>

            <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-5">
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card p-5 lg:col-span-3">
                <div className="flex items-baseline justify-between">
                  <h4 className="text-[13.5px] font-semibold text-ink-950">Tokens por día</h4>
                  <span className="text-[12px] text-mist-500">Últimos 14 días</span>
                </div>
                <div className="mt-4 h-60">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={series} margin={{ left: -8, right: 4, top: 6 }}>
                      <defs>
                        <linearGradient id="homeTokens" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#E3622E" stopOpacity={0.28} />
                          <stop offset="100%" stopColor="#E3622E" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid vertical={false} stroke={GRID} />
                      <XAxis dataKey="date" tickFormatter={fmtDay} tick={AXIS} axisLine={false} tickLine={false} minTickGap={24} />
                      <YAxis tickFormatter={fmtCompact} tick={AXIS} axisLine={false} tickLine={false} width={44} />
                      <RTooltip content={<ChartTooltip />} cursor={{ stroke: "#D9D6CD" }} />
                      <Area type="monotone" dataKey="tokens" name="Tokens" stroke="#E3622E" strokeWidth={2} fill="url(#homeTokens)" animationDuration={900} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </motion.div>

              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="card p-5 lg:col-span-2">
                <h4 className="text-[13.5px] font-semibold text-ink-950">Agentes con mayor consumo</h4>
                <div className="mt-4 space-y-3.5">
                  {topAgents.map((a, i) => (
                    <button key={a.agent_id} onClick={() => navigate(`/agentes/${a.agent_id}`)} className="focus-ring group block w-full text-left">
                      <div className="flex items-center gap-2.5">
                        <AgentIcon name={agentById[a.agent_id]?.icon} size="sm" />
                        <span className="flex-1 truncate text-[13px] font-medium text-ink-950 group-hover:text-accent-dark">{a.agent_name}</span>
                        <span className="text-[12px] tabular text-mist-500">{fmtCompact(a.tokens)}</span>
                      </div>
                      <div className="ml-[38px] mt-1.5 h-1.5 overflow-hidden rounded-full bg-mist-100">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${(a.tokens / maxTokens) * 100}%` }}
                          transition={{ duration: 0.8, delay: 0.3 + i * 0.06, ease: [0.22, 1, 0.36, 1] }}
                          className={`h-full rounded-full ${i === 0 ? "bg-accent" : "bg-ink-950/80"}`}
                        />
                      </div>
                    </button>
                  ))}
                  {!topAgents.length && <p className="text-[13px] text-mist-500">Sin actividad todavía.</p>}
                </div>
              </motion.div>
            </div>

            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="card mt-3">
              <div className="flex items-center justify-between px-5 pt-5">
                <h4 className="text-[13.5px] font-semibold text-ink-950">Actividad reciente</h4>
              </div>
              <div className="mt-2 divide-y divide-mist-100">
                {activity.map((ev) => (
                  <div key={ev.id} className="flex items-center gap-3 px-5 py-3">
                    <AgentIcon name={agentById[ev.agent_id]?.icon} size="sm" />
                    <div className="min-w-0 flex-1 text-[13px]">
                      <span className="font-medium text-ink-950">{ev.agent_name}</span>
                      <span className="text-mist-500"> respondió a {ev.user_name || "un usuario"}</span>
                    </div>
                    {ev.success ? (
                      <span className="hidden font-mono text-[11.5px] text-mist-500 sm:block">{fmtNumber(ev.tokens)} tok · {fmtLatency(ev.latency_ms)}</span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11.5px] text-red-600"><CircleAlert size={12} /> Sin respuesta</span>
                    )}
                    <span className="w-20 text-right text-[11.5px] text-mist-400">{fmtRelative(ev.created_at)}</span>
                  </div>
                ))}
                {!activity.length && <p className="px-5 py-6 text-[13px] text-mist-500">Aún no hay actividad.</p>}
              </div>
            </motion.div>
          </>
        ) : (
          <>
            <h3 className="mt-10 text-[15px] font-semibold text-ink-950">Agentes disponibles</h3>
            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {agents.filter((a) => a.status === "active").map((a, i) => (
                <AgentCard key={a.id} agent={a} index={i} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

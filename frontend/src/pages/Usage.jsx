import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip as RTooltip, XAxis, YAxis } from "recharts";
import { Coins, MessagesSquare, Timer, CircleAlert, PiggyBank, ArrowDownUp } from "lucide-react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import StatTile from "../components/StatTile";
import Avatar from "../components/Avatar";
import ChartTooltip, { AXIS, GRID } from "../components/ChartTooltip";
import { AgentIcon } from "../lib/icons";
import { listAgents, listUsers, metricsSummary, metricsTimeseries } from "../api/client";
import { fmtCompact, fmtDay, fmtLatency, fmtNumber, fmtPct, fmtUSD } from "../lib/format";

const RANGES = [
  { days: 7, label: "7 días" },
  { days: 30, label: "30 días" },
  { days: 90, label: "90 días" },
];

const COLUMNS = [
  { key: "name", label: "Agente" },
  { key: "requests", label: "Solicitudes" },
  { key: "prompt_tokens", label: "Entrada" },
  { key: "completion_tokens", label: "Salida" },
  { key: "tokens", label: "Total" },
  { key: "avg_latency_ms", label: "Latencia" },
  { key: "errors", label: "Errores" },
  { key: "cloud_cost_usd", label: "Costo nube" },
];

function Breakdown({ title, rows, render, delay }) {
  const total = rows.reduce((a, r) => a + r.tokens, 0) || 1;
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }} className="card p-5">
      <h4 className="text-[13.5px] font-semibold text-ink-950">{title}</h4>
      <div className="mt-4 space-y-3">
        {rows.map((r, i) => (
          <div key={r.key}>
            <div className="flex items-center gap-2.5">
              {render(r)}
              <span className="ml-auto text-[12px] tabular text-mist-500">{fmtCompact(r.tokens)}</span>
              <span className="w-12 text-right text-[12px] font-medium tabular text-ink-950">{Math.round((r.tokens / total) * 100)}%</span>
            </div>
            <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-mist-100">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(r.tokens / total) * 100}%` }}
                transition={{ duration: 0.8, delay: delay + i * 0.05 }}
                className={`h-full rounded-full ${i === 0 ? "bg-accent" : "bg-ink-950/70"}`}
              />
            </div>
          </div>
        ))}
        {!rows.length && <p className="text-[13px] text-mist-500">Sin datos en el periodo.</p>}
      </div>
    </motion.div>
  );
}

export default function Usage() {
  const navigate = useNavigate();
  const [days, setDays] = useState(30);
  const [summary, setSummary] = useState(null);
  const [series, setSeries] = useState([]);
  const [agents, setAgents] = useState([]);
  const [users, setUsers] = useState([]);
  const [sort, setSort] = useState({ key: "tokens", dir: -1 });

  useEffect(() => {
    listAgents().then(setAgents).catch(() => {});
    listUsers().then(setUsers).catch(() => {});
  }, []);

  useEffect(() => {
    metricsSummary(days).then(setSummary).catch(() => {});
    metricsTimeseries(days).then(setSeries).catch(() => {});
  }, [days]);

  const agentById = useMemo(() => Object.fromEntries(agents.map((a) => [a.id, a])), [agents]);
  const userById = useMemo(() => Object.fromEntries(users.map((u) => [u.id, u])), [users]);

  const rows = useMemo(() => {
    const list = [...(summary?.agents_breakdown || [])];
    list.sort((a, b) => {
      const av = a[sort.key];
      const bv = b[sort.key];
      return (typeof av === "string" ? av.localeCompare(bv) : av - bv) * sort.dir;
    });
    return list;
  }, [summary, sort]);
  const maxTokens = Math.max(1, ...rows.map((r) => r.tokens));

  return (
    <div>
      <PageHeader
        title="Consumo"
        description="Tokens, rendimiento y costos por agente"
        actions={
          <div className="inline-flex rounded-lg border border-mist-200 bg-white p-0.5">
            {RANGES.map((r) => (
              <button
                key={r.days}
                onClick={() => setDays(r.days)}
                className={`focus-ring rounded-md px-3 py-1.5 text-[12.5px] font-medium transition ${days === r.days ? "bg-ink-950 text-white" : "text-mist-500 hover:text-ink-950"}`}
              >
                {r.label}
              </button>
            ))}
          </div>
        }
      />
      <div className="mx-auto max-w-[1200px] space-y-3 px-8 py-8">
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
          <StatTile label="Tokens totales" icon={Coins} value={summary?.total_tokens} format={fmtCompact} highlight
            sub={summary && `${fmtCompact(summary.prompt_tokens)} entrada · ${fmtCompact(summary.completion_tokens)} salida`} />
          <StatTile label="Solicitudes" icon={MessagesSquare} value={summary?.total_requests} format={fmtNumber} delay={0.04}
            sub={summary && `${fmtNumber(summary.tool_calls)} usos de herramientas`} />
          <StatTile label="Latencia promedio" icon={Timer} value={summary ? fmtLatency(summary.avg_latency_ms) : null} delay={0.08} />
          <StatTile label="Tasa de error" icon={CircleAlert} value={summary ? fmtPct(summary.error_rate) : null} delay={0.12} />
          <StatTile label="Costo evitado" icon={PiggyBank} value={summary?.estimated_cloud_cost_usd} format={fmtUSD} delay={0.16}
            hint={summary && `Costo estimado del mismo consumo en un proveedor en la nube (${fmtUSD(summary.cloud_price_per_1k)} por 1K tokens). El costo local es $0.`}
            sub="Costo local: $0.00" />
        </div>

        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="card p-5">
          <div className="flex items-baseline justify-between">
            <h4 className="text-[13.5px] font-semibold text-ink-950">Tokens por día</h4>
            <div className="flex items-center gap-4 text-[12px] text-mist-500">
              <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-accent" /> Entrada</span>
              <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-ink-950" /> Salida</span>
            </div>
          </div>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={series} margin={{ left: -8, right: 4, top: 6 }} barCategoryGap={days > 30 ? 1 : "22%"}>
                <CartesianGrid vertical={false} stroke={GRID} />
                <XAxis dataKey="date" tickFormatter={fmtDay} tick={AXIS} axisLine={false} tickLine={false} minTickGap={28} />
                <YAxis tickFormatter={fmtCompact} tick={AXIS} axisLine={false} tickLine={false} width={44} />
                <RTooltip content={<ChartTooltip />} cursor={{ fill: "#F4F3EF" }} />
                <Bar dataKey="prompt_tokens" name="Entrada" stackId="t" fill="#E3622E" />
                <Bar dataKey="completion_tokens" name="Salida" stackId="t" fill="#141413" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card overflow-hidden">
          <div className="px-5 pt-5">
            <h4 className="text-[13.5px] font-semibold text-ink-950">Consumo por agente</h4>
          </div>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="border-y border-mist-100 bg-mist-50/60 text-left text-[11.5px] text-mist-500">
                  {COLUMNS.map((c) => (
                    <th key={c.key} className={`px-4 py-2.5 font-medium ${c.key === "name" ? "pl-5" : "text-right"}`}>
                      <button
                        onClick={() => setSort((s) => ({ key: c.key, dir: s.key === c.key ? -s.dir : -1 }))}
                        className={`focus-ring inline-flex items-center gap-1 rounded hover:text-ink-950 ${sort.key === c.key ? "text-ink-950" : ""}`}
                      >
                        {c.label}
                        <ArrowDownUp size={11} className={sort.key === c.key ? "opacity-100" : "opacity-30"} />
                      </button>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-mist-100">
                {rows.map((r) => (
                  <tr key={r.agent_id} onClick={() => agentById[r.agent_id] && navigate(`/agentes/${r.agent_id}`)}
                    className={`transition ${agentById[r.agent_id] ? "cursor-pointer hover:bg-mist-50" : ""}`}>
                    <td className="py-3 pl-5 pr-4">
                      <div className="flex items-center gap-2.5">
                        <AgentIcon name={agentById[r.agent_id]?.icon} size="sm" />
                        <span className="font-medium text-ink-950">{r.agent_name}</span>
                      </div>
                    </td>
                    <td className="px-4 text-right tabular text-ink-700">{fmtNumber(r.requests)}</td>
                    <td className="px-4 text-right tabular text-ink-700">{fmtNumber(r.prompt_tokens)}</td>
                    <td className="px-4 text-right tabular text-ink-700">{fmtNumber(r.completion_tokens)}</td>
                    <td className="px-4 text-right">
                      <div className="flex items-center justify-end gap-2.5">
                        <div className="hidden h-1.5 w-16 overflow-hidden rounded-full bg-mist-100 md:block">
                          <div className="h-full rounded-full bg-accent" style={{ width: `${(r.tokens / maxTokens) * 100}%` }} />
                        </div>
                        <span className="font-medium tabular text-ink-950">{fmtNumber(r.tokens)}</span>
                      </div>
                    </td>
                    <td className="px-4 text-right tabular text-ink-700">{fmtLatency(r.avg_latency_ms)}</td>
                    <td className={`px-4 text-right tabular ${r.errors ? "text-red-600" : "text-mist-400"}`}>{r.errors}</td>
                    <td className="px-4 text-right tabular text-ink-700">{fmtUSD(r.cloud_cost_usd)}</td>
                  </tr>
                ))}
                {!rows.length && (
                  <tr><td colSpan={COLUMNS.length} className="px-5 py-8 text-center text-mist-500">Sin actividad en el periodo.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          <Breakdown
            title="Por usuario"
            delay={0.25}
            rows={summary?.users_breakdown || []}
            render={(r) => (
              <>
                <Avatar name={r.name} role={userById[r.key]?.role} size="xs" />
                <span className="text-[13px] font-medium text-ink-950">{r.name}</span>
              </>
            )}
          />
          <Breakdown
            title="Por modelo"
            delay={0.3}
            rows={summary?.models_breakdown || []}
            render={(r) => <span className="font-mono text-[12.5px] text-ink-950">{r.name}</span>}
          />
        </div>
      </div>
    </div>
  );
}

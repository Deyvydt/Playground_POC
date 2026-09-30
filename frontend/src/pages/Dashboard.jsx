import { useEffect, useState } from "react";
import {
  BarChart, Bar, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { Bot, MessagesSquare, Timer, PiggyBank } from "lucide-react";
import TopBar from "../components/TopBar";
import StatTile from "../components/StatTile";
import EmptyState from "../components/EmptyState";
import { metricsSummary, metricsTimeseries } from "../api/client";

const CATEGORICAL = ["#5F68C3", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#4a3aa7"];

function ChartCard({ title, sub, children, empty }) {
  return (
    <div className="rounded-2xl border border-mist-200 bg-white p-5 shadow-soft">
      <div className="mb-4">
        <h3 className="text-[13.5px] font-semibold text-ink-950">{title}</h3>
        {sub && <p className="text-[12px] text-mist-500">{sub}</p>}
      </div>
      {empty ? (
        <div className="flex h-56 items-center justify-center text-[12.5px] text-mist-400">
          Aún no hay actividad registrada — prueba un agente en el Playground.
        </div>
      ) : (
        <div className="h-56">{children}</div>
      )}
    </div>
  );
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-mist-200 bg-white px-3 py-2 text-[12px] shadow-card">
      <div className="font-medium text-ink-950">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="text-mist-500">
          {p.name}: <span className="tabular font-medium text-ink-950">{p.value}</span>
        </div>
      ))}
    </div>
  );
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [series, setSeries] = useState([]);

  useEffect(() => {
    metricsSummary().then(setSummary).catch(() => setSummary(null));
    metricsTimeseries().then(setSeries).catch(() => setSeries([]));
  }, []);

  const hasActivity = (summary?.total_requests || 0) > 0;
  const savings = summary ? (summary.estimated_cloud_cost_usd - summary.local_cost_usd) : 0;

  return (
    <div>
      <TopBar title="Panel de administración" description="Consumo, rendimiento y actividad de todos los agentes" />
      <div className="mx-auto max-w-6xl space-y-6 px-8 py-8">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatTile label="Agentes activos" value={summary?.total_agents ?? "—"} icon={Bot} accent />
          <StatTile label="Conversaciones" value={summary?.total_conversations ?? "—"} icon={MessagesSquare} />
          <StatTile
            label="Latencia promedio"
            value={summary ? `${summary.avg_latency_ms} ms` : "—"}
            icon={Timer}
            sub={hasActivity ? "por respuesta" : undefined}
          />
          <StatTile
            label="Costo local vs. nube"
            value={summary ? "$0.00" : "—"}
            icon={PiggyBank}
            sub={hasActivity ? `Ahorro estimado: $${savings.toFixed(4)} (ref. nube $${summary.estimated_cloud_cost_usd})` : "sin actividad aún"}
            accent
          />
        </div>

        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          <ChartCard title="Solicitudes por día" sub="Últimos 7 días" empty={!hasActivity}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={series} barSize={22}>
                <CartesianGrid vertical={false} stroke="#e4e4e7" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#898781" }} axisLine={{ stroke: "#e4e4e7" }} tickLine={false} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#898781" }} axisLine={false} tickLine={false} width={28} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f4f4f5" }} />
                <Bar dataKey="requests" name="Solicitudes" radius={[4, 4, 0, 0]} fill="#5F68C3" />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Tokens consumidos" sub="Últimos 7 días · procesados localmente" empty={!hasActivity}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={series}>
                <defs>
                  <linearGradient id="tokenFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#5F68C3" stopOpacity={0.28} />
                    <stop offset="100%" stopColor="#5F68C3" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="#e4e4e7" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#898781" }} axisLine={{ stroke: "#e4e4e7" }} tickLine={false} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#898781" }} axisLine={false} tickLine={false} width={36} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="tokens" name="Tokens" stroke="#5F68C3" strokeWidth={2} fill="url(#tokenFill)" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        <ChartCard title="Solicitudes por agente" sub="Distribución de uso" empty={!hasActivity}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={summary?.agents_breakdown || []} layout="vertical" barSize={18}>
              <CartesianGrid horizontal={false} stroke="#e4e4e7" />
              <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: "#898781" }} axisLine={false} tickLine={false} />
              <YAxis dataKey="agent_name" type="category" width={130} tick={{ fontSize: 12, fill: "#0b0b0b" }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f4f4f5" }} />
              <Bar dataKey="requests" name="Solicitudes" radius={[0, 4, 4, 0]}>
                {(summary?.agents_breakdown || []).map((_, i) => (
                  <Cell key={i} fill={CATEGORICAL[i % CATEGORICAL.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Check, Cpu, Minus, RefreshCw, ShieldCheck, Wrench, UserRound, Database } from "lucide-react";
import PageHeader from "../components/PageHeader";
import Badge from "../components/Badge";
import Avatar from "../components/Avatar";
import Tooltip from "../components/Tooltip";
import { useSession } from "../context/SessionContext";
import { health, listModels, listTools } from "../api/client";
import { ROLES, PERMISSION_LABELS } from "../lib/roles";
import { ROLE_LABEL } from "../lib/format";
import api from "../api/client";

function Section({ icon: Icon, title, description, action, children, delay = 0 }) {
  return (
    <motion.section initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }} className="card">
      <div className="flex items-start justify-between gap-4 border-b border-mist-100 px-5 py-4">
        <div className="flex items-start gap-3">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-mist-100 text-ink-800"><Icon size={15} /></span>
          <div>
            <h3 className="text-[14px] font-semibold text-ink-950">{title}</h3>
            {description && <p className="text-[12.5px] text-mist-500">{description}</p>}
          </div>
        </div>
        {action}
      </div>
      <div className="p-5">{children}</div>
    </motion.section>
  );
}

export default function SettingsPage() {
  const { currentUser } = useSession();
  const [models, setModels] = useState([]);
  const [tools, setTools] = useState([]);
  const [roles, setRoles] = useState({});
  const [engineUp, setEngineUp] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const refresh = async () => {
    setRefreshing(true);
    await Promise.all([
      listModels().then(setModels).catch(() => setModels([])),
      health().then((d) => setEngineUp(d.ollama_available)).catch(() => setEngineUp(false)),
    ]);
    setRefreshing(false);
  };

  useEffect(() => {
    refresh();
    listTools().then(setTools).catch(() => {});
    api.get("/roles").then((r) => setRoles(r.data)).catch(() => {});
  }, []);

  return (
    <div>
      <PageHeader title="Configuración" description="Tu cuenta, modelos, herramientas y permisos" />
      <div className="mx-auto max-w-[1000px] space-y-4 px-8 py-8">
        <Section icon={UserRound} title="Tu cuenta">
          <div className="flex items-center gap-4">
            <Avatar name={currentUser.name} role={currentUser.role} size="lg" />
            <div>
              <p className="text-[15px] font-semibold text-ink-950">{currentUser.name}</p>
              <p className="text-[13px] text-mist-500">{currentUser.email}</p>
            </div>
            <div className="ml-auto text-right">
              <Badge tone="dark">{ROLE_LABEL[currentUser.role]}</Badge>
              {currentUser.title && <p className="mt-1 text-[12px] text-mist-500">{currentUser.title}</p>}
            </div>
          </div>
        </Section>

        <Section
          icon={Cpu}
          title="Motor de modelos"
          description="Modelos instalados en la infraestructura propia"
          delay={0.05}
          action={
            <div className="flex items-center gap-2">
              {engineUp !== null && (engineUp ? <Badge tone="good" dot>En línea</Badge> : <Badge tone="critical" dot>Sin conexión</Badge>)}
              <Tooltip label="Actualizar">
                <button onClick={refresh} className="btn-icon"><RefreshCw size={14} className={refreshing ? "animate-spin" : ""} /></button>
              </Tooltip>
            </div>
          }
        >
          {models.length === 0 ? (
            <p className="text-[13px] text-mist-500">{engineUp === false ? "No se puede contactar al motor de modelos." : "No hay modelos instalados."}</p>
          ) : (
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {models.map((m) => (
                <div key={m.name} className="flex items-center gap-3 rounded-lg border border-mist-200 px-3.5 py-3">
                  <span className="grid h-8 w-8 place-items-center rounded-md bg-ink-950 text-white">
                    {m.embedding ? <Database size={14} /> : <Cpu size={14} />}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-mono text-[12.5px] text-ink-950">{m.name}</p>
                    <p className="text-[11.5px] text-mist-500">
                      {m.embedding ? "Embeddings · conocimiento" : "Conversación"}
                      {m.parameters && ` · ${m.parameters}`}
                    </p>
                  </div>
                  <span className="font-mono text-[11.5px] text-mist-400">{m.size ? `${(m.size / 1e9).toFixed(1)} GB` : ""}</span>
                </div>
              ))}
            </div>
          )}
        </Section>

        <Section icon={Wrench} title="Herramientas" description="Funciones que los agentes pueden invocar" delay={0.1}>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            {tools.map((t) => (
              <div key={t.name} className="rounded-lg border border-mist-200 px-3.5 py-3">
                <p className="font-mono text-[12.5px] text-ink-950">{t.name}</p>
                <p className="mt-1 text-[12px] leading-snug text-mist-500">{t.description}</p>
              </div>
            ))}
          </div>
        </Section>

        <Section icon={ShieldCheck} title="Roles y permisos" description="Qué puede hacer cada rol" delay={0.15}>
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="text-left text-[12px] text-mist-500">
                  <th className="pb-3 font-medium">Permiso</th>
                  {ROLES.map((r) => (
                    <th key={r.id} className="pb-3 text-center font-medium">
                      <span className={currentUser.role === r.id ? "text-ink-950" : ""}>{r.label}</span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-mist-100">
                {PERMISSION_LABELS.map((p) => (
                  <tr key={p.id}>
                    <td className="py-2.5 text-ink-800">{p.label}</td>
                    {ROLES.map((r) => (
                      <td key={r.id} className="text-center">
                        {roles[r.id]?.includes(p.id) ? (
                          <Check size={15} className="mx-auto text-accent" strokeWidth={2.5} />
                        ) : (
                          <Minus size={14} className="mx-auto text-mist-300" />
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      </div>
    </div>
  );
}

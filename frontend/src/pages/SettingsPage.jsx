import { useEffect, useState } from "react";
import { ShieldCheck, Cpu, Check } from "lucide-react";
import TopBar from "../components/TopBar";
import Badge from "../components/Badge";
import { useSession } from "../context/SessionContext";
import { listModels, health } from "../api/client";

const ROLE_INFO = {
  admin: {
    label: "Administrador",
    desc: "Acceso total: crear, editar y eliminar agentes, gestionar usuarios y ver todas las métricas.",
    perms: ["Crear / editar agentes", "Eliminar agentes", "Gestionar conocimiento (RAG)", "Ver métricas", "Chatear"],
  },
  developer: {
    label: "Desarrollador",
    desc: "Puede construir y probar agentes, pero no eliminarlos ni administrar usuarios.",
    perms: ["Crear / editar agentes", "Gestionar conocimiento (RAG)", "Ver métricas", "Chatear"],
  },
  viewer: {
    label: "Solo lectura",
    desc: "Puede usar los agentes existentes en el playground, sin permisos de administración.",
    perms: ["Chatear con agentes"],
  },
};

export default function SettingsPage() {
  const { users, currentUser, switchUser } = useSession();
  const [models, setModels] = useState([]);
  const [ollamaUp, setOllamaUp] = useState(null);

  useEffect(() => {
    listModels().then(setModels).catch(() => setModels([]));
    health().then((d) => setOllamaUp(d.ollama_available)).catch(() => setOllamaUp(false));
  }, []);

  return (
    <div>
      <TopBar title="Configuración" description="Control de accesos (RBAC) y estado del motor de modelos locales" />
      <div className="mx-auto max-w-5xl space-y-6 px-8 py-8">
        <section className="rounded-2xl border border-mist-200 bg-white p-5">
          <div className="mb-4 flex items-center gap-2">
            <Cpu size={16} className="text-tcs" />
            <h3 className="text-[13.5px] font-semibold text-ink-950">Motor de modelos (Ollama · local)</h3>
            <Badge tone={ollamaUp ? "good" : "critical"} dot>{ollamaUp ? "Conectado" : "Desconectado"}</Badge>
          </div>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {models.length === 0 && <p className="text-[12.5px] text-mist-500">No se detectaron modelos locales.</p>}
            {models.map((m) => (
              <div key={m.name} className="flex items-center justify-between rounded-xl bg-mist-50 px-3.5 py-2.5">
                <span className="text-[13px] font-medium text-ink-950">{m.name}</span>
                <span className="text-[11.5px] text-mist-500">{(m.size / 1e9).toFixed(1)} GB</span>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-mist-200 bg-white p-5">
          <div className="mb-4 flex items-center gap-2">
            <ShieldCheck size={16} className="text-tcs" />
            <h3 className="text-[13.5px] font-semibold text-ink-950">Control de accesos (RBAC)</h3>
          </div>
          <p className="mb-4 text-[12.5px] text-mist-500">
            Simulación de roles para la demo — en producción se integraría con el directorio corporativo (SSO/AD) de TCS.
          </p>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            {Object.entries(ROLE_INFO).map(([role, info]) => (
              <div key={role} className="rounded-2xl border border-mist-200 p-4">
                <h4 className="text-[13px] font-semibold text-ink-950">{info.label}</h4>
                <p className="mt-1 text-[12px] text-mist-500">{info.desc}</p>
                <ul className="mt-3 space-y-1.5">
                  {info.perms.map((p) => (
                    <li key={p} className="flex items-center gap-1.5 text-[12px] text-ink-800">
                      <Check size={12} className="text-emerald-600" /> {p}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-mist-200 bg-white p-5">
          <h3 className="mb-4 text-[13.5px] font-semibold text-ink-950">Usuarios de demostración</h3>
          <div className="divide-y divide-mist-100">
            {users.map((u) => (
              <div key={u.id} className="flex items-center justify-between py-3">
                <div className="flex items-center gap-3">
                  <span className="grid h-9 w-9 place-items-center rounded-full bg-mist-100 text-base">{u.avatar_emoji}</span>
                  <div>
                    <p className="text-[13px] font-medium text-ink-950">{u.name}</p>
                    <p className="text-[11.5px] text-mist-500">{u.title} · {ROLE_INFO[u.role]?.label}</p>
                  </div>
                </div>
                <button
                  onClick={() => switchUser(u)}
                  className={`focus-ring rounded-lg border px-3 py-1.5 text-[12px] font-medium ${
                    currentUser.id === u.id ? "border-tcs bg-tcs-50 text-tcs-dark" : "border-mist-200 text-ink-950 hover:bg-mist-50"
                  }`}
                >
                  {currentUser.id === u.id ? "Sesión activa" : "Usar esta sesión"}
                </button>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ShieldCheck, Shuffle, Users, SlidersHorizontal, ArrowRight,
  Settings2, Database, MessagesSquare, Gauge, DollarSign,
} from "lucide-react";
import Logo from "../components/Logo";

const BENEFITS = [
  {
    icon: ShieldCheck,
    title: "Privacidad de datos",
    desc: "Los prompts, documentos y conversaciones de TCS nunca salen de nuestra infraestructura ni entrenan modelos de terceros.",
  },
  {
    icon: Shuffle,
    title: "Independencia de proveedores",
    desc: "Cambiamos de modelo (local o en la nube) con un clic si un proveedor cambia precios o condiciones.",
  },
  {
    icon: Users,
    title: "Colaboración multi-agente",
    desc: "Un agente Analista puede entregarle su resultado a un agente Redactor, encadenando tareas complejas.",
  },
  {
    icon: SlidersHorizontal,
    title: "Personalización absoluta",
    desc: "Diseñamos la interfaz y el comportamiento exactamente como lo necesitan nuestros equipos internos.",
  },
];

const STEPS = [
  { icon: Settings2, title: "Crear y configurar", desc: "Rol, modelo y herramientas de cada agente." },
  { icon: Database, title: "Conectar conocimiento", desc: "Documentos internos vía RAG y memoria." },
  { icon: MessagesSquare, title: "Probar en vivo", desc: "Chat con traza de razonamiento paso a paso." },
  { icon: Gauge, title: "Monitorear y administrar", desc: "Costos, latencia y accesos por rol (RBAC)." },
];

export default function Overview() {
  const navigate = useNavigate();

  return (
    <div className="mx-auto max-w-6xl px-8 py-14">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <div className="mb-8 flex items-center justify-between">
          <Logo />
          <span className="rounded-full border border-mist-200 bg-white px-3 py-1 text-[11px] font-medium text-mist-500">
            Propuesta interna · Prototipo (POC)
          </span>
        </div>

        <div className="max-w-3xl">
          <h1 className="text-[38px] font-bold leading-[1.1] tracking-tight text-ink-950">
            Nuestro propio entorno para crear y administrar{" "}
            <span className="text-tcs">agentes de IA</span>
          </h1>
          <p className="mt-4 text-[15.5px] leading-relaxed text-mist-500">
            Una plataforma privada, desplegada en nuestra propia infraestructura, para diseñar, probar y
            gobernar agentes de inteligencia artificial con modelos locales — sin depender de un playground
            público ni exponer información confidencial a terceros.
          </p>
          <div className="mt-7 flex flex-wrap items-center gap-3">
            <button
              onClick={() => navigate("/panel")}
              className="focus-ring inline-flex items-center gap-2 rounded-xl bg-ink-950 px-5 py-3 text-[13.5px] font-semibold text-white transition hover:bg-ink-800"
            >
              Ver el panel en vivo <ArrowRight size={15} />
            </button>
            <button
              onClick={() => navigate("/agentes")}
              className="focus-ring inline-flex items-center gap-2 rounded-xl border border-mist-300 bg-white px-5 py-3 text-[13.5px] font-semibold text-ink-950 transition hover:bg-mist-50"
            >
              Explorar agentes de ejemplo
            </button>
          </div>
        </div>
      </motion.div>

      {/* Beneficios */}
      <section className="mt-16">
        <h2 className="text-[12px] font-semibold uppercase tracking-wide text-mist-400">
          Por qué construir nuestro propio playground
        </h2>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {BENEFITS.map((b, i) => (
            <motion.div
              key={b.title}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, delay: i * 0.06 }}
              className="rounded-2xl border border-mist-200 bg-white p-5 shadow-soft"
            >
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-tcs-50 text-tcs">
                <b.icon size={18} />
              </span>
              <h3 className="mt-3.5 text-[14px] font-semibold text-ink-950">{b.title}</h3>
              <p className="mt-1.5 text-[12.5px] leading-relaxed text-mist-500">{b.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Cómo funciona */}
      <section className="mt-14">
        <h2 className="text-[12px] font-semibold uppercase tracking-wide text-mist-400">Cómo funciona</h2>
        <div className="relative mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((s, i) => (
            <div key={s.title} className="relative rounded-2xl border border-mist-200 bg-white p-5">
              <div className="flex items-center gap-3">
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-ink-950 text-[12px] font-semibold text-white">
                  {i + 1}
                </span>
                <s.icon size={17} className="text-tcs" />
              </div>
              <h3 className="mt-3 text-[13.5px] font-semibold text-ink-950">{s.title}</h3>
              <p className="mt-1 text-[12.5px] text-mist-500">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Ahorro de costos */}
      <section className="mt-14 overflow-hidden rounded-2xl border border-mist-200 bg-ink-950 p-8 text-white">
        <div className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
          <div>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-2.5 py-1 text-[11px] font-medium">
              <DollarSign size={12} /> Impacto económico estimado
            </span>
            <h3 className="mt-3 text-[20px] font-semibold">Modelos locales, costo marginal $0 por consulta</h3>
            <p className="mt-1.5 max-w-lg text-[13px] text-white/60">
              Al ejecutar los modelos en nuestra propia infraestructura (Ollama), evitamos el costo por
              token de las APIs comerciales para casos de uso internos de alto volumen.
            </p>
          </div>
          <button
            onClick={() => navigate("/panel")}
            className="focus-ring shrink-0 rounded-xl bg-white px-5 py-3 text-[13px] font-semibold text-ink-950 hover:bg-mist-100"
          >
            Ver métricas de consumo
          </button>
        </div>
      </section>

      <footer className="mt-14 flex items-center justify-between border-t border-mist-200 pt-6 text-[12px] text-mist-400">
        <span>TCS Agent Playground — prototipo interno de evaluación</span>
        <span>Metodología SDD · GitHub Spec Kit</span>
      </footer>
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Lock, Check, Loader2, Bot, DollarSign, ShieldCheck, ArrowRight } from "lucide-react";
import { useSession } from "../context/SessionContext";

const ROLE_LABEL = { admin: "Administrador", developer: "Desarrollador", viewer: "Solo lectura" };

const STATS = [
  { icon: ShieldCheck, label: "Datos 100% locales" },
  { icon: DollarSign, label: "$0 costo marginal" },
  { icon: Bot, label: "4 agentes activos" },
];

function BrandPanel() {
  const panelRef = useRef(null);

  const handleMouseMove = (e) => {
    const el = panelRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    el.style.setProperty("--mx", x.toFixed(3));
    el.style.setProperty("--my", y.toFixed(3));
  };

  return (
    <div
      ref={panelRef}
      onMouseMove={handleMouseMove}
      className="relative hidden w-1/2 overflow-hidden bg-ink-950 lg:flex lg:items-center lg:justify-center"
    >
      <div className="blob-field absolute inset-0">
        <span className="blob blob-1" />
        <span className="blob blob-2" />
        <span className="blob blob-3" />
      </div>
      <div className="brand-grid absolute inset-0" />
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-ink-950 via-transparent to-ink-950/40" />

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="relative z-10 max-w-md px-12 text-white"
      >
        <img
          src="/tcs-logo.svg"
          alt="TCS"
          className="h-8 w-auto"
          style={{ filter: "brightness(0) invert(1)" }}
        />

        <motion.h1
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="mt-9 text-[32px] font-bold leading-[1.15] tracking-tight"
        >
          Nuestro propio{" "}
          <span className="shimmer-text">entorno de agentes de IA</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-4 text-[14px] leading-relaxed text-white/55"
        >
          Un espacio privado para crear, probar y administrar agentes internos
          de TCS — sin que un solo dato salga de nuestra infraestructura.
        </motion.p>

        <div className="mt-9 flex flex-col gap-2.5">
          {STATS.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.45, delay: 0.45 + i * 0.1 }}
              className="flex items-center gap-2.5 rounded-xl border border-white/10 bg-white/[0.04] px-3.5 py-2.5 backdrop-blur-sm"
            >
              <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-white/10 text-tcs-light">
                <s.icon size={13} />
              </span>
              <span className="text-[12.5px] font-medium text-white/80">{s.label}</span>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

export default function Login() {
  const { users, login } = useSession();
  const [selected, setSelected] = useState(null);
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("idle"); // idle | loading | success

  useEffect(() => {
    if (users?.length && !selected) setSelected(users[0]);
  }, [users]); // eslint-disable-line react-hooks/exhaustive-deps

  const canSubmit = selected && password.trim().length > 0 && status === "idle";

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!canSubmit) return;
    setStatus("loading");
    setTimeout(() => {
      setStatus("success");
      setTimeout(() => login(selected), 550);
    }, 700);
  };

  return (
    <motion.div
      exit={{ opacity: 0, scale: 1.02 }}
      transition={{ duration: 0.4, ease: "easeIn" }}
      className="flex h-screen w-full overflow-hidden bg-white"
    >
      <BrandPanel />

      <div className="flex w-full items-center justify-center overflow-y-auto bg-mist-50 px-6 py-10 lg:w-1/2">
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-sm"
        >
          <div className="mb-8 flex items-center gap-2.5 lg:hidden">
            <img src="/tcs-logo.svg" alt="TCS" className="h-6 w-auto" />
            <span className="text-[13px] font-semibold text-ink-950">Agent Playground</span>
          </div>

          <h2 className="text-[22px] font-bold tracking-tight text-ink-950">Bienvenido de vuelta</h2>
          <p className="mt-1.5 text-[13.5px] text-mist-500">
            Selecciona tu perfil para acceder al entorno de agentes.
          </p>

          <form onSubmit={handleSubmit} className="mt-7 space-y-5">
            <div>
              <label className="mb-2 block text-[11.5px] font-semibold uppercase tracking-wide text-mist-400">
                Perfil
              </label>
              <div className="space-y-2">
                {users.map((u, i) => (
                  <motion.button
                    type="button"
                    key={u.id}
                    onClick={() => setSelected(u)}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.35, delay: 0.1 + i * 0.06 }}
                    whileHover={{ y: -1 }}
                    whileTap={{ scale: 0.98 }}
                    className={`focus-ring flex w-full items-center gap-3 rounded-xl border px-3.5 py-2.5 text-left transition-colors ${
                      selected?.id === u.id
                        ? "border-tcs bg-tcs-50 shadow-soft"
                        : "border-mist-200 bg-white hover:border-mist-300"
                    }`}
                  >
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-mist-100 text-base">
                      {u.avatar_emoji}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-[13px] font-medium text-ink-950">{u.name}</span>
                      <span className="block text-[11.5px] text-mist-500">
                        {u.title} · {ROLE_LABEL[u.role]}
                      </span>
                    </span>
                    <span
                      className={`grid h-5 w-5 shrink-0 place-items-center rounded-full border-2 transition-colors ${
                        selected?.id === u.id ? "border-tcs bg-tcs" : "border-mist-300"
                      }`}
                    >
                      {selected?.id === u.id && <Check size={11} className="text-white" strokeWidth={3} />}
                    </span>
                  </motion.button>
                ))}
              </div>
            </div>

            <div>
              <label className="mb-2 block text-[11.5px] font-semibold uppercase tracking-wide text-mist-400">
                Contraseña
              </label>
              <div className="relative">
                <Lock size={15} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-mist-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="focus-ring w-full rounded-xl border border-mist-200 bg-white py-2.5 pl-10 pr-3.5 text-[13.5px]"
                />
              </div>
              <p className="mt-1.5 text-[11px] text-mist-400">
                Prototipo interno — cualquier contraseña es válida.
              </p>
            </div>

            <motion.button
              type="submit"
              disabled={!canSubmit}
              whileTap={canSubmit ? { scale: 0.98 } : {}}
              className="focus-ring flex w-full items-center justify-center gap-2 rounded-xl bg-ink-950 py-3 text-[13.5px] font-semibold text-white transition hover:bg-ink-800 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <AnimatePresence mode="wait" initial={false}>
                {status === "idle" && (
                  <motion.span
                    key="idle"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center gap-2"
                  >
                    Iniciar sesión <ArrowRight size={14} />
                  </motion.span>
                )}
                {status === "loading" && (
                  <motion.span
                    key="loading"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center gap-2"
                  >
                    <Loader2 size={15} className="animate-spin" /> Verificando…
                  </motion.span>
                )}
                {status === "success" && (
                  <motion.span
                    key="success"
                    initial={{ opacity: 0, scale: 0.7 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex items-center gap-2"
                  >
                    <Check size={15} strokeWidth={3} /> Acceso concedido
                  </motion.span>
                )}
              </AnimatePresence>
            </motion.button>
          </form>

          <p className="mt-8 text-center text-[11px] text-mist-400">
            TCS Agent Playground — acceso interno de evaluación (POC)
          </p>
        </motion.div>
      </div>
    </motion.div>
  );
}

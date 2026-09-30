import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, Check, Eye, EyeOff, Loader2, Lock, Mail, ShieldCheck, Activity, Coins } from "lucide-react";
import NetworkCanvas from "../components/NetworkCanvas";
import Logo from "../components/Logo";
import Avatar from "../components/Avatar";
import { useSession } from "../context/SessionContext";
import { errorMessage } from "../api/client";

const HIGHLIGHTS = [
  { icon: ShieldCheck, label: "Tus datos no salen de la organización" },
  { icon: Activity, label: "Cada respuesta, trazable paso a paso" },
  { icon: Coins, label: "Consumo de tokens bajo control" },
];

// Accesos rápidos a las cuentas habituales del equipo.
const RECENT_ACCOUNTS = [
  { name: "Ana Ríos", email: "ana.rios@tcs.com", role: "admin" },
  { name: "Carlos Vega", email: "carlos.vega@tcs.com", role: "developer" },
  { name: "Lucía Soto", email: "lucia.soto@tcs.com", role: "viewer" },
];

function BrandPanel() {
  return (
    <div className="relative hidden w-[52%] overflow-hidden bg-ink-950 lg:block">
      <NetworkCanvas className="absolute inset-0 h-full w-full" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_30%_40%,transparent_0%,rgba(20,20,19,0.55)_55%,rgba(20,20,19,0.95)_100%)]" />
      <div className="pointer-events-none absolute -bottom-40 -left-24 h-[420px] w-[420px] rounded-full bg-accent/25 blur-[120px]" />

      <div className="pointer-events-none relative z-10 flex h-full flex-col justify-between p-12">
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="flex items-center gap-4">
          <img src="/tcs-logo.svg" alt="Tata Consultancy Services" className="h-16 w-auto" style={{ filter: "brightness(0) invert(1)" }} />
          <span className="h-10 w-px bg-white/20" />
          <span className="text-[15px] font-semibold tracking-tight text-white">Agent Playground</span>
        </motion.div>

        <div className="max-w-xl">
          <motion.h1
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="font-serif text-[56px] leading-[1.02] tracking-[-0.01em] text-white"
          >
            Todos tus agentes de IA,
            <br />
            <span className="italic text-accent-light">en un solo lugar.</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="mt-5 max-w-md text-[15px] leading-relaxed text-white/55"
          >
            Crea, prueba y gobierna agentes con modelos que corren en tu propia infraestructura.
          </motion.p>

          <div className="mt-10 space-y-3">
            {HIGHLIGHTS.map((h, i) => (
              <motion.div
                key={h.label}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.5 + i * 0.1 }}
                className="flex items-center gap-3 text-[13.5px] text-white/75"
              >
                <span className="grid h-7 w-7 place-items-center rounded-lg border border-white/10 bg-white/5 text-accent-light">
                  <h.icon size={14} />
                </span>
                {h.label}
              </motion.div>
            ))}
          </div>
        </div>

        <p className="text-[12px] text-white/35">© {new Date().getFullYear()} Tata Consultancy Services</p>
      </div>
    </div>
  );
}

export default function Login() {
  const { login } = useSession();
  const [email, setEmail] = useState(() => {
    try {
      return localStorage.getItem("ap-last-email") || "";
    } catch {
      return "";
    }
  });
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(true);
  const [status, setStatus] = useState("idle"); // idle | loading | success
  const [error, setError] = useState("");
  const [shakeKey, setShakeKey] = useState(0);
  const passwordRef = useRef(null);
  const emailRef = useRef(null);

  useEffect(() => {
    (email ? passwordRef : emailRef).current?.focus();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (status !== "idle") return;
    if (!email.trim() || !password) {
      setError("Ingresa tu correo y contraseña.");
      setShakeKey((k) => k + 1);
      return;
    }
    setError("");
    setStatus("loading");
    try {
      const finish = await login(email.trim(), password, remember);
      setStatus("success");
      setTimeout(finish, 650);
    } catch (err) {
      setStatus("idle");
      setError(errorMessage(err, "No pudimos conectar con el servidor. Intenta nuevamente."));
      setShakeKey((k) => k + 1);
    }
  };

  const pickAccount = (account) => {
    setEmail(account.email);
    setError("");
    passwordRef.current?.focus();
  };

  return (
    <motion.div
      exit={{ opacity: 0 }}
      transition={{ duration: 0.35 }}
      className="flex h-screen w-full overflow-hidden bg-white"
    >
      <BrandPanel />

      <div className="relative flex flex-1 items-center justify-center overflow-y-auto px-6 py-10">
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
          className="w-full max-w-[380px]"
        >
          <div className="mb-10 lg:hidden">
            <Logo />
          </div>

          <h2 className="text-[26px] font-semibold tracking-tight text-ink-950">Inicia sesión</h2>
          <p className="mt-1.5 text-[14px] text-mist-500">Accede con tu cuenta corporativa.</p>

          <motion.form key={shakeKey} onSubmit={handleSubmit} className={`mt-8 space-y-4 ${shakeKey ? "animate-shake" : ""}`} noValidate>
            <div>
              <label className="label" htmlFor="email">Correo electrónico</label>
              <div className="relative">
                <Mail size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-mist-400" />
                <input
                  id="email"
                  ref={emailRef}
                  type="email"
                  autoComplete="username"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="nombre@tcs.com"
                  className="input h-11 pl-9"
                />
              </div>
            </div>

            <div>
              <label className="label" htmlFor="password">Contraseña</label>
              <div className="relative">
                <Lock size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-mist-400" />
                <input
                  id="password"
                  ref={passwordRef}
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="input h-11 pl-9 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="focus-ring absolute right-2 top-1/2 grid h-7 w-7 -translate-y-1/2 place-items-center rounded-md text-mist-400 hover:text-ink-950"
                  aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                  title={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            <label className="flex cursor-pointer select-none items-center gap-2 text-[13px] text-ink-700">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="h-4 w-4 rounded border-mist-300 accent-ink-950"
              />
              Mantener la sesión iniciada
            </label>

            <AnimatePresence>
              {error && (
                <motion.p
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="rounded-lg bg-red-50 px-3 py-2 text-[12.5px] text-red-700"
                  role="alert"
                >
                  {error}
                </motion.p>
              )}
            </AnimatePresence>

            <button
              type="submit"
              disabled={status !== "idle"}
              className={`btn h-11 w-full text-[14px] text-white shadow-soft ${
                status === "success" ? "bg-emerald-600" : "bg-ink-950 hover:bg-ink-800"
              } disabled:cursor-default disabled:opacity-100`}
            >
              <AnimatePresence mode="wait" initial={false}>
                {status === "idle" && (
                  <motion.span key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex items-center gap-2">
                    Continuar <ArrowRight size={15} />
                  </motion.span>
                )}
                {status === "loading" && (
                  <motion.span key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex items-center gap-2">
                    <Loader2 size={15} className="animate-spin" /> Verificando
                  </motion.span>
                )}
                {status === "success" && (
                  <motion.span key="success" initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} className="flex items-center gap-2">
                    <Check size={15} strokeWidth={3} /> Bienvenido
                  </motion.span>
                )}
              </AnimatePresence>
            </button>
          </motion.form>

          <div className="mt-9">
            <div className="flex items-center gap-3">
              <span className="h-px flex-1 bg-mist-200" />
              <span className="text-[11.5px] text-mist-400">Cuentas recientes</span>
              <span className="h-px flex-1 bg-mist-200" />
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2">
              {RECENT_ACCOUNTS.map((a, i) => (
                <motion.button
                  key={a.email}
                  type="button"
                  onClick={() => pickAccount(a)}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.35 + i * 0.06 }}
                  whileHover={{ y: -2 }}
                  title={a.email}
                  className={`focus-ring flex flex-col items-center gap-1.5 rounded-xl border px-2 py-3 transition-colors ${
                    email === a.email ? "border-ink-950 bg-mist-50" : "border-mist-200 hover:border-mist-300"
                  }`}
                >
                  <Avatar name={a.name} role={a.role} size="md" />
                  <span className="w-full truncate text-center text-[12px] font-medium text-ink-950">{a.name.split(" ")[0]}</span>
                </motion.button>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}

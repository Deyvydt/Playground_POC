import { useEffect, useRef, useState } from "react";
import { ChevronDown, LogOut } from "lucide-react";
import { useSession } from "../context/SessionContext";
import { health } from "../api/client";
import Badge from "./Badge";

const ROLE_LABEL = { admin: "Administrador", developer: "Desarrollador", viewer: "Solo lectura" };

export default function TopBar({ title, description }) {
  const { users, currentUser, switchUser, logout } = useSession();
  const [open, setOpen] = useState(false);
  const [ollamaUp, setOllamaUp] = useState(null);
  const ref = useRef(null);

  useEffect(() => {
    health().then((d) => setOllamaUp(d.ollama_available)).catch(() => setOllamaUp(false));
    const id = setInterval(() => {
      health().then((d) => setOllamaUp(d.ollama_available)).catch(() => setOllamaUp(false));
    }, 15000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const onClick = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-mist-200 bg-white/80 px-6 backdrop-blur">
      <div>
        <h1 className="text-[15px] font-semibold text-ink-950">{title}</h1>
        {description && <p className="text-[12.5px] text-mist-500">{description}</p>}
      </div>
      <div className="flex items-center gap-3">
        <Badge tone={ollamaUp ? "good" : "critical"} dot>
          {ollamaUp === null ? "Verificando..." : ollamaUp ? "Ollama conectado" : "Ollama desconectado"}
        </Badge>

        <div className="relative" ref={ref}>
          <button
            onClick={() => setOpen((v) => !v)}
            className="focus-ring flex items-center gap-2 rounded-full border border-mist-200 bg-white py-1 pl-1 pr-2.5 hover:bg-mist-50"
          >
            <span className="grid h-7 w-7 place-items-center rounded-full bg-mist-100 text-sm">
              {currentUser.avatar_emoji}
            </span>
            <span className="text-left leading-tight">
              <span className="block text-[12.5px] font-medium text-ink-950">{currentUser.name}</span>
              <span className="block text-[10.5px] text-mist-500">{ROLE_LABEL[currentUser.role]}</span>
            </span>
            <ChevronDown size={13} className="text-mist-400" />
          </button>
          {open && (
            <div className="absolute right-0 z-20 mt-2 w-60 rounded-xl border border-mist-200 bg-white p-1.5 shadow-card animate-fadeUp">
              <p className="px-2.5 py-1.5 text-[10.5px] font-medium uppercase tracking-wide text-mist-400">
                Simular sesión como
              </p>
              {users.map((u) => (
                <button
                  key={u.id}
                  onClick={() => { switchUser(u); setOpen(false); }}
                  className={`focus-ring flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-[13px] hover:bg-mist-50 ${
                    u.id === currentUser.id ? "bg-tcs-50" : ""
                  }`}
                >
                  <span className="grid h-7 w-7 place-items-center rounded-full bg-mist-100 text-sm">{u.avatar_emoji}</span>
                  <span>
                    <span className="block font-medium text-ink-950">{u.name}</span>
                    <span className="block text-[11px] text-mist-500">{u.title} · {ROLE_LABEL[u.role]}</span>
                  </span>
                </button>
              ))}
              <div className="my-1 h-px bg-mist-100" />
              <button
                onClick={() => { setOpen(false); logout(); }}
                className="focus-ring flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-[13px] font-medium text-red-600 hover:bg-red-50"
              >
                <span className="grid h-7 w-7 place-items-center rounded-full bg-red-50">
                  <LogOut size={13} />
                </span>
                Cerrar sesión
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

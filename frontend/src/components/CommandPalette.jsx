import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { CornerDownLeft, LogOut, Plus, Search } from "lucide-react";
import { NAV_ITEMS } from "../lib/nav";
import { AgentIcon } from "../lib/icons";
import { listAgents } from "../api/client";
import { useSession } from "../context/SessionContext";

export default function CommandPalette({ open, onClose }) {
  const navigate = useNavigate();
  const { can, logout } = useSession();
  const [query, setQuery] = useState("");
  const [agents, setAgents] = useState([]);
  const [active, setActive] = useState(0);
  const inputRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    setQuery("");
    setActive(0);
    listAgents().then(setAgents).catch(() => {});
    setTimeout(() => inputRef.current?.focus(), 30);
  }, [open]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    const match = (s) => !q || s.toLowerCase().includes(q);
    const pages = NAV_ITEMS.filter((i) => (!i.permission || can(i.permission)) && match(i.label)).map((i) => ({
      group: "Ir a",
      label: i.label,
      icon: <i.icon size={15} className="text-mist-500" />,
      run: () => navigate(i.to),
    }));
    const agentItems = agents
      .filter((a) => match(a.name) || match(a.description || ""))
      .map((a) => ({
        group: "Agentes",
        label: a.name,
        detail: a.description,
        icon: <AgentIcon name={a.icon} size="sm" />,
        run: () => navigate(`/agentes/${a.id}`),
      }));
    const actions = [
      can("create") && { label: "Crear agente", icon: <Plus size={15} className="text-mist-500" />, run: () => navigate("/agentes?nuevo=1") },
      { label: "Cerrar sesión", icon: <LogOut size={15} className="text-mist-500" />, run: logout },
    ]
      .filter(Boolean)
      .filter((a) => match(a.label))
      .map((a) => ({ ...a, group: "Acciones" }));
    return [...pages, ...agentItems, ...actions];
  }, [query, agents, can, navigate, logout]);

  const select = (item) => {
    onClose();
    item?.run();
  };

  const onKeyDown = (e) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => Math.min(results.length - 1, i + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(0, i - 1));
    } else if (e.key === "Enter") {
      select(results[active]);
    } else if (e.key === "Escape") {
      onClose();
    }
  };

  let lastGroup = null;

  return (
    <AnimatePresence>
      {open && (
        <motion.div className="fixed inset-0 z-[70] flex items-start justify-center px-4 pt-[14vh]" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <div className="absolute inset-0 bg-ink-950/25 backdrop-blur-[2px]" onClick={onClose} />
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.98 }}
            transition={{ type: "spring", stiffness: 480, damping: 36 }}
            className="relative w-full max-w-xl overflow-hidden rounded-2xl border border-mist-200 bg-white shadow-pop"
          >
            <div className="flex items-center gap-3 border-b border-mist-100 px-4">
              <Search size={16} className="text-mist-400" />
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setActive(0);
                }}
                onKeyDown={onKeyDown}
                placeholder="Busca agentes, páginas o acciones…"
                className="h-14 flex-1 bg-transparent text-[14.5px] text-ink-950 placeholder:text-mist-400 focus:outline-none"
              />
              <kbd className="rounded border border-mist-200 px-1.5 font-mono text-[10px] text-mist-400">Esc</kbd>
            </div>
            <div className="max-h-[360px] overflow-y-auto p-2">
              {results.length === 0 && <p className="px-3 py-8 text-center text-[13px] text-mist-500">Sin resultados para “{query}”</p>}
              {results.map((item, i) => {
                const header = item.group !== lastGroup ? item.group : null;
                lastGroup = item.group;
                return (
                  <div key={`${item.group}-${item.label}`}>
                    {header && <p className="eyebrow px-2.5 pb-1 pt-2.5">{header}</p>}
                    <button
                      onMouseEnter={() => setActive(i)}
                      onClick={() => select(item)}
                      className={`flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-left ${i === active ? "bg-mist-100" : ""}`}
                    >
                      <span className="grid h-7 w-7 shrink-0 place-items-center">{item.icon}</span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-[13.5px] text-ink-950">{item.label}</span>
                        {item.detail && <span className="block truncate text-[11.5px] text-mist-500">{item.detail}</span>}
                      </span>
                      {i === active && <CornerDownLeft size={13} className="text-mist-400" />}
                    </button>
                  </div>
                );
              })}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

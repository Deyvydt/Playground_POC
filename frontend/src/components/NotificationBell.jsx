import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Bell, CheckCheck } from "lucide-react";
import Tooltip from "./Tooltip";
import { govMarkAllRead, govMarkRead, govNotifications } from "../api/client";
import { fmtRelative } from "../lib/format";

const POLL_MS = 30000;
const DOT = { info: "bg-mist-400", warning: "bg-amber-500", critical: "bg-red-500" };

export default function NotificationBell() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const load = useCallback(() => govNotifications(30).then(setData).catch(() => setData(null)), []);

  useEffect(() => {
    load();
    const id = setInterval(load, POLL_MS);
    return () => clearInterval(id);
  }, [load]);

  useEffect(() => {
    const onClick = (e) => ref.current && !ref.current.contains(e.target) && setOpen(false);
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  // Sin servicio de gobierno no hay avisos que mostrar: la campana no aparece.
  if (!data) return null;

  const openItem = async (n) => {
    if (!n.read) await govMarkRead(n.id).catch(() => {});
    setOpen(false);
    load();
    navigate(n.agente_id ? `/gobierno?agente=${n.agente_id}` : "/gobierno");
  };

  const readAll = async () => {
    await govMarkAllRead().catch(() => {});
    load();
  };

  return (
    <div className="relative" ref={ref}>
      <Tooltip label="Avisos de gobierno" side="bottom" disabled={open}>
        <button onClick={() => setOpen((v) => !v)} className={`btn-icon relative ${open ? "bg-mist-100 text-ink-950" : ""}`}>
          <Bell size={16} />
          {data.unread > 0 && (
            <span className="absolute -right-0.5 -top-0.5 grid h-4 min-w-4 place-items-center rounded-full bg-accent px-1 text-[10px] font-semibold tabular text-white">
              {data.unread > 9 ? "9+" : data.unread}
            </span>
          )}
        </button>
      </Tooltip>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -4, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.14 }}
            className="absolute right-0 top-full z-50 mt-2 w-[340px] overflow-hidden rounded-xl border border-mist-200 bg-white shadow-pop"
          >
            <div className="flex items-center justify-between border-b border-mist-100 px-4 py-3">
              <p className="text-[13px] font-semibold text-ink-950">Avisos</p>
              <button onClick={readAll} disabled={!data.unread} className="btn-ghost -mr-1.5 py-1 text-[12px]">
                <CheckCheck size={14} /> Marcar todo leído
              </button>
            </div>
            <div className="max-h-[380px] overflow-y-auto">
              {data.items.length === 0 && <p className="px-4 py-8 text-center text-[12.5px] text-mist-500">Sin avisos por ahora.</p>}
              {data.items.map((n) => (
                <button
                  key={n.id}
                  onClick={() => openItem(n)}
                  className={`focus-ring flex w-full gap-3 border-b border-mist-100 px-4 py-3 text-left transition last:border-0 hover:bg-mist-50 ${
                    n.read ? "" : "bg-accent-50/40"
                  }`}
                >
                  <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${DOT[n.severity] || DOT.info}`} />
                  <span className="min-w-0 flex-1">
                    <span className={`block truncate text-[12.5px] ${n.read ? "text-ink-700" : "font-semibold text-ink-950"}`}>{n.title}</span>
                    {n.message && <span className="mt-0.5 block line-clamp-2 text-[12px] text-mist-500">{n.message}</span>}
                    <span className="mt-1 block text-[11px] text-mist-400">{fmtRelative(n.created_at)}</span>
                  </span>
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

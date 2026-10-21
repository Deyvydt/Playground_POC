import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronsUpDown, LogOut, Settings, ShieldCheck } from "lucide-react";
import Avatar from "./Avatar";
import Tooltip from "./Tooltip";
import { useSession } from "../context/SessionContext";
import { ROLE_LABEL } from "../lib/format";

export default function UserMenu({ collapsed }) {
  const { currentUser, logout } = useSession();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const onClick = (e) => ref.current && !ref.current.contains(e.target) && setOpen(false);
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  if (!currentUser) return null;

  return (
    <div className="relative" ref={ref}>
      <Tooltip label={`${currentUser.name} · ${ROLE_LABEL[currentUser.role]}`} side="right" disabled={!collapsed || open}>
        <button
          onClick={() => setOpen((v) => !v)}
          className={`focus-ring flex w-full items-center gap-2.5 rounded-lg transition hover:bg-mist-50 ${
            collapsed ? "mx-auto h-9 w-9 justify-center" : "px-1.5 py-1.5"
          } ${open ? "bg-mist-50" : ""}`}
        >
          <Avatar name={currentUser.name} role={currentUser.role} size="sm" />
          {!collapsed && (
            <>
              <span className="min-w-0 flex-1 text-left leading-tight">
                <span className="block truncate text-[12.5px] font-medium text-ink-950">{currentUser.name}</span>
                <span className="block truncate text-[11px] text-mist-500">{ROLE_LABEL[currentUser.role]}</span>
              </span>
              <ChevronsUpDown size={14} className="text-mist-400" />
            </>
          )}
        </button>
      </Tooltip>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4 }}
            transition={{ duration: 0.14 }}
            className={`absolute bottom-full z-50 mb-2 w-60 rounded-xl border border-mist-200 bg-white p-1.5 shadow-pop ${
              collapsed ? "left-0" : "left-0 right-0 w-auto"
            }`}
          >
            <div className="px-2.5 py-2">
              <p className="text-[13px] font-medium text-ink-950">{currentUser.name}</p>
              <p className="truncate text-[11.5px] text-mist-500">{currentUser.email}</p>
              <p className="mt-1.5 inline-flex items-center gap-1 text-[11px] text-mist-500">
                <ShieldCheck size={12} className="text-accent" /> {ROLE_LABEL[currentUser.role]}
                {currentUser.title && ` · ${currentUser.title}`}
              </p>
            </div>
            <div className="my-1 h-px bg-mist-100" />
            <button
              onClick={() => {
                setOpen(false);
                navigate("/configuracion");
              }}
              className="focus-ring flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-[13px] text-ink-800 hover:bg-mist-50"
            >
              <Settings size={14} className="text-mist-500" /> Configuración
            </button>
            <button
              onClick={() => {
                setOpen(false);
                logout();
              }}
              className="focus-ring flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-[13px] text-red-600 hover:bg-red-50"
            >
              <LogOut size={14} /> Cerrar sesión
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

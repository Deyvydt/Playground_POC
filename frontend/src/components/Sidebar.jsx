import { NavLink } from "react-router-dom";
import { motion } from "framer-motion";
import { PanelLeftClose, PanelLeftOpen, Search } from "lucide-react";
import Logo from "./Logo";
import Tooltip from "./Tooltip";
import UserMenu from "./UserMenu";
import { NAV_ITEMS } from "../lib/nav";
import { useSession } from "../context/SessionContext";

export default function Sidebar({ collapsed, onToggle, onOpenPalette }) {
  const { can } = useSession();
  const items = NAV_ITEMS.filter((i) => !i.permission || can(i.permission));

  return (
    <motion.aside
      animate={{ width: collapsed ? 68 : 244 }}
      transition={{ type: "spring", stiffness: 380, damping: 38 }}
      className="relative z-20 flex h-screen shrink-0 flex-col border-r border-mist-200 bg-white"
    >
      <div className={`flex h-16 items-center ${collapsed ? "justify-center" : "justify-between pl-5 pr-3"}`}>
        {collapsed ? <Logo collapsed /> : <Logo />}
      </div>

      <div className={`px-3 pb-2 ${collapsed ? "flex justify-center" : ""}`}>
        <Tooltip label="Buscar" shortcut="Ctrl K" side="right" disabled={!collapsed}>
          <button
            onClick={onOpenPalette}
            className={`focus-ring flex items-center gap-2 rounded-lg border border-mist-200 bg-mist-50 text-[12.5px] text-mist-500 transition hover:border-mist-300 hover:text-ink-950 ${
              collapsed ? "h-9 w-9 justify-center" : "w-full px-2.5 py-1.5"
            }`}
          >
            <Search size={14} />
            {!collapsed && (
              <>
                <span className="flex-1 text-left">Buscar…</span>
                <kbd className="rounded border border-mist-200 bg-white px-1.5 font-mono text-[10px] text-mist-400">Ctrl K</kbd>
              </>
            )}
          </button>
        </Tooltip>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto overflow-x-hidden px-3 py-2 scrollbar-none">
        {!collapsed && <p className="eyebrow px-2.5 pb-1.5 pt-2">Espacio de trabajo</p>}
        {items.map(({ to, label, icon: Icon, end, hint }) => (
          <Tooltip key={to} label={collapsed ? label : hint} side="right">
            <NavLink
              to={to}
              end={end}
              className={({ isActive }) =>
                `focus-ring group relative flex items-center gap-2.5 rounded-lg text-[13.5px] font-medium transition-colors ${
                  collapsed ? "mx-auto h-9 w-9 justify-center" : "px-2.5 py-2"
                } ${isActive ? "bg-mist-100 text-ink-950" : "text-mist-500 hover:bg-mist-50 hover:text-ink-950"}`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.span
                      layoutId="nav-indicator"
                      className={`absolute rounded-full bg-accent ${collapsed ? "-left-3 h-5 w-[3px]" : "-left-3 h-5 w-[3px]"}`}
                      transition={{ type: "spring", stiffness: 500, damping: 36 }}
                    />
                  )}
                  <Icon size={17} strokeWidth={isActive ? 2 : 1.75} className={isActive ? "text-ink-950" : ""} />
                  {!collapsed && <span className="truncate">{label}</span>}
                </>
              )}
            </NavLink>
          </Tooltip>
        ))}
      </nav>

      <div className="border-t border-mist-100 p-3">
        <UserMenu collapsed={collapsed} />
        <Tooltip label={collapsed ? "Expandir menú" : "Contraer menú"} shortcut="Ctrl B" side="right">
          <button
            onClick={onToggle}
            className={`focus-ring mt-1 flex items-center gap-2.5 rounded-lg text-[12.5px] text-mist-500 transition hover:bg-mist-50 hover:text-ink-950 ${
              collapsed ? "mx-auto h-9 w-9 justify-center" : "w-full px-2.5 py-2"
            }`}
          >
            {collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
            {!collapsed && "Contraer"}
          </button>
        </Tooltip>
      </div>
    </motion.aside>
  );
}

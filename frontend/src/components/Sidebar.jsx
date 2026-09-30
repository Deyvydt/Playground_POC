import { NavLink } from "react-router-dom";
import { LayoutGrid, Bot, Workflow, Gauge, Settings, Sparkles } from "lucide-react";
import Logo from "./Logo";

const ITEMS = [
  { to: "/", label: "Resumen", icon: Sparkles, end: true },
  { to: "/panel", label: "Panel", icon: Gauge },
  { to: "/agentes", label: "Agentes", icon: Bot },
  { to: "/flujo", label: "Flujo Multi-Agente", icon: Workflow },
  { to: "/configuracion", label: "Configuración", icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-mist-200 bg-white">
      <div className="flex h-16 items-center border-b border-mist-100 px-5">
        <Logo />
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `focus-ring flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-[13.5px] font-medium transition ${
                isActive
                  ? "bg-ink-950 text-white"
                  : "text-mist-500 hover:bg-mist-100 hover:text-ink-950"
              }`
            }
          >
            <Icon size={16} strokeWidth={2} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-mist-100 p-4">
        <div className="flex items-center gap-2 rounded-xl bg-mist-50 px-3 py-2.5">
          <LayoutGrid size={14} className="text-tcs" />
          <div className="text-[11px] leading-tight text-mist-500">
            <div className="font-medium text-ink-800">POC interno</div>
            100% modelos locales
          </div>
        </div>
      </div>
    </aside>
  );
}

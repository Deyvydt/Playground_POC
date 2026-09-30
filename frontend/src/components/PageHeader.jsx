import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Tooltip from "./Tooltip";
import { health } from "../api/client";

function EngineStatus() {
  const [up, setUp] = useState(null);

  useEffect(() => {
    const check = () => health().then((d) => setUp(d.ollama_available)).catch(() => setUp(false));
    check();
    const id = setInterval(check, 15000);
    return () => clearInterval(id);
  }, []);

  const label = up === null ? "Verificando motor…" : up ? "Motor de modelos en línea" : "Motor de modelos sin conexión";
  return (
    <Tooltip label={up ? "Los agentes pueden responder" : "Los agentes no podrán responder hasta restablecer la conexión"} side="bottom">
      <span className="inline-flex cursor-default items-center gap-2 rounded-full border border-mist-200 bg-white px-2.5 py-1 text-[11.5px] font-medium text-ink-700">
        <span className="relative flex h-2 w-2">
          {up && <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />}
          <span className={`relative inline-flex h-2 w-2 rounded-full ${up === null ? "bg-mist-300" : up ? "bg-emerald-500" : "bg-red-500"}`} />
        </span>
        {label}
      </span>
    </Tooltip>
  );
}

export default function PageHeader({ title, description, actions, eyebrow }) {
  return (
    <header className="sticky top-0 z-10 border-b border-mist-200/80 bg-mist-50/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between gap-4 px-8">
        <motion.div initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.3 }} className="min-w-0">
          {eyebrow && <div className="text-[11.5px] text-mist-500">{eyebrow}</div>}
          <h1 className="truncate text-[16px] font-semibold tracking-tight text-ink-950">{title}</h1>
          {description && !eyebrow && <p className="truncate text-[12.5px] text-mist-500">{description}</p>}
        </motion.div>
        <div className="flex shrink-0 items-center gap-2.5">
          <EngineStatus />
          {actions}
        </div>
      </div>
    </header>
  );
}

import { motion } from "framer-motion";
import AnimatedNumber from "./AnimatedNumber";
import Tooltip from "./Tooltip";
import { Info } from "lucide-react";

export default function StatTile({ label, value, format, sub, icon: Icon, hint, delay = 0, highlight = false }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className={`group relative overflow-hidden rounded-xl border p-4 transition-shadow hover:shadow-card ${
        highlight ? "border-ink-950 bg-ink-950 text-white" : "border-mist-200 bg-white"
      }`}
    >
      <div className="flex items-center justify-between">
        <span className={`flex items-center gap-1.5 text-[12px] font-medium ${highlight ? "text-white/60" : "text-mist-500"}`}>
          {Icon && <Icon size={14} strokeWidth={1.75} className={highlight ? "text-accent-light" : "text-mist-400"} />}
          {label}
        </span>
        {hint && (
          <Tooltip label={hint}>
            <button className={`focus-ring rounded ${highlight ? "text-white/40 hover:text-white" : "text-mist-300 hover:text-ink-950"}`}>
              <Info size={13} />
            </button>
          </Tooltip>
        )}
      </div>
      <div className="mt-2.5 text-[26px] font-semibold leading-none tracking-tight">
        {typeof value === "number" ? <AnimatedNumber value={value} format={format} /> : value ?? "—"}
      </div>
      {sub && <div className={`mt-2 text-[12px] ${highlight ? "text-white/55" : "text-mist-500"}`}>{sub}</div>}
    </motion.div>
  );
}

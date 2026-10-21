import { fmtDay, fmtNumber } from "../lib/format";

export default function ChartTooltip({ active, payload, label, isDate = true, formatter = fmtNumber }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-mist-200 bg-white px-3 py-2 text-[12px] shadow-pop">
      <div className="mb-1 font-medium text-ink-950">{isDate ? fmtDay(label) : label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="flex items-center gap-2 text-mist-500">
          <span className="h-2 w-2 rounded-sm" style={{ background: p.color || p.fill }} />
          {p.name}
          <span className="ml-auto pl-4 font-medium tabular text-ink-950">{formatter(p.value)}</span>
        </div>
      ))}
    </div>
  );
}

export const AXIS = { fontSize: 11, fill: "#A3A097", fontFamily: "Geist Variable" };
export const GRID = "#EEECE6";
export const SERIES = ["#E3622E", "#141413", "#A3A097", "#F2A07A", "#5A5852", "#D9D6CD"];

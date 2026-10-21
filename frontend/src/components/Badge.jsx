const STYLES = {
  neutral: "bg-mist-100 text-ink-700 ring-mist-200",
  accent: "bg-accent-50 text-accent-dark ring-accent-100",
  dark: "bg-ink-950 text-white ring-ink-950",
  good: "bg-emerald-50 text-emerald-700 ring-emerald-100",
  warning: "bg-amber-50 text-amber-700 ring-amber-100",
  critical: "bg-red-50 text-red-700 ring-red-100",
};

export default function Badge({ children, tone = "neutral", dot = false, className = "" }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset ${STYLES[tone]} ${className}`}
    >
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
}

export default function EmptyState({ icon: Icon, title, description, action, compact = false }) {
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-xl border border-dashed border-mist-300 bg-white/50 px-6 text-center ${
        compact ? "py-8" : "py-14"
      }`}
    >
      {Icon && (
        <span className="mb-3 grid h-10 w-10 place-items-center rounded-xl bg-white text-ink-700 shadow-soft ring-1 ring-mist-200">
          <Icon size={18} strokeWidth={1.75} />
        </span>
      )}
      <p className="text-[14px] font-semibold text-ink-950">{title}</p>
      {description && <p className="mt-1 max-w-sm text-[13px] text-mist-500">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

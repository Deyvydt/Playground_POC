export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-mist-300 bg-white/60 px-6 py-14 text-center">
      {Icon && (
        <span className="mb-3 grid h-11 w-11 place-items-center rounded-full bg-mist-100 text-mist-500">
          <Icon size={20} />
        </span>
      )}
      <p className="text-sm font-semibold text-ink-950">{title}</p>
      {description && <p className="mt-1 max-w-sm text-[13px] text-mist-500">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

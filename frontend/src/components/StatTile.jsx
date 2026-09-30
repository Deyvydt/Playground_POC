export default function StatTile({ label, value, sub, icon: Icon, accent = false }) {
  return (
    <div className="rounded-2xl border border-mist-200 bg-white p-5 shadow-soft animate-fadeUp">
      <div className="flex items-start justify-between">
        <span className="text-[12.5px] font-medium text-mist-500">{label}</span>
        {Icon && (
          <span
            className={`grid h-8 w-8 place-items-center rounded-full ${
              accent ? "bg-tcs-50 text-tcs" : "bg-mist-100 text-mist-500"
            }`}
          >
            <Icon size={16} strokeWidth={2} />
          </span>
        )}
      </div>
      <div className="mt-3 text-2xl font-semibold tabular text-ink-950">{value}</div>
      {sub && <div className="mt-1 text-[12px] text-mist-500">{sub}</div>}
    </div>
  );
}

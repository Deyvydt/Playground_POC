export default function Logo({ compact = false }) {
  return (
    <div className="flex items-center gap-2.5">
      <img src="/tcs-logo.svg" alt="TCS" className="h-6 w-auto shrink-0" />
      {!compact && (
        <div className="leading-tight">
          <div className="text-[13px] font-semibold text-ink-950 tracking-tight">Agent Playground</div>
          <div className="text-[10.5px] text-mist-500 -mt-0.5">Interno · Prototipo</div>
        </div>
      )}
    </div>
  );
}

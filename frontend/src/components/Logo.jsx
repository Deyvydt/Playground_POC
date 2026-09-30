export default function Logo({ collapsed = false, inverted = false }) {
  const filter = inverted ? { filter: "brightness(0) invert(1)" } : undefined;
  if (collapsed) {
    return <img src="/tcs-mark.svg" alt="TCS" className="h-7 w-auto" style={filter} />;
  }
  return (
    <div className="flex items-center gap-3">
      <img src="/tcs-mark.svg" alt="Tata Consultancy Services" className="h-8 w-auto shrink-0" style={filter} />
      <span className={`h-6 w-px ${inverted ? "bg-white/20" : "bg-mist-300"}`} />
      <span
        className={`whitespace-nowrap text-[13px] font-semibold tracking-tight ${inverted ? "text-white" : "text-ink-950"}`}
      >
        Agent Playground
      </span>
    </div>
  );
}

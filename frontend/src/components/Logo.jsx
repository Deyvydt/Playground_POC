import { useId } from "react";

// Marca "IO": una barra (I) junto a un anillo (O), sobre un degradado de la paleta accent.
export function TokenMark({ size = 32, className = "" }) {
  const id = useId();
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" className={`shrink-0 ${className}`} role="img" aria-label="TokenIO">
      <defs>
        <linearGradient id={id} x1="4" y1="2" x2="28" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#F28A5C" />
          <stop offset="1" stopColor="#B94A1C" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill={`url(#${id})`} />
      <rect x="7.5" y="9" width="3.4" height="14" rx="1.7" fill="#fff" />
      <circle cx="20.5" cy="16" r="5.3" fill="none" stroke="#fff" strokeWidth="3.4" />
    </svg>
  );
}

const SIZES = {
  md: { mark: 32, text: "text-[21px]" },
  xl: { mark: 52, text: "text-[38px]" },
};

export function Wordmark({ inverted = false, size = "md" }) {
  return (
    <span className={`whitespace-nowrap font-sans font-extrabold leading-none tracking-[-0.045em] ${SIZES[size].text} ${inverted ? "text-white" : "text-ink-950"}`}>
      Token
      <span className="bg-gradient-to-br from-accent-light to-accent-dark bg-clip-text text-transparent">IO</span>
    </span>
  );
}

// TCS es el branding de la empresa; TokenIO es el nombre del producto.
export default function Logo({ collapsed = false, inverted = false, size = "md" }) {
  const filter = inverted ? { filter: "brightness(0) invert(1)" } : undefined;
  if (collapsed) {
    return <img src="/tcs-mark.svg" alt="TCS" className="h-7 w-auto" style={filter} />;
  }
  const big = size === "xl";
  return (
    <div className={`flex items-center ${big ? "gap-4" : "gap-3"}`}>
      <img
        src={big ? "/tcs-logo.svg" : "/tcs-mark.svg"}
        alt="Tata Consultancy Services"
        className={`${big ? "h-16" : "h-8"} w-auto shrink-0`}
        style={filter}
      />
      <span className={`${big ? "h-10" : "h-6"} w-px ${inverted ? "bg-white/20" : "bg-mist-300"}`} />
      <Wordmark inverted={inverted} size={size} />
    </div>
  );
}

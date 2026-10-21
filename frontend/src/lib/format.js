const nf = new Intl.NumberFormat("es-PE");
const compact = new Intl.NumberFormat("es-PE", { notation: "compact", maximumFractionDigits: 1 });
const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2 });

export const fmtNumber = (n) => nf.format(Math.round(n || 0));
export const fmtCompact = (n) => compact.format(n || 0);
export const fmtUSD = (n) => usd.format(n || 0);
export const fmtPct = (n) => `${((n || 0) * 100).toFixed(1)}%`;

export const fmtLatency = (ms) => {
  if (ms == null) return "—";
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)} s` : `${ms} ms`;
};

// El backend guarda fechas en UTC sin zona; se fuerza la interpretación UTC.
export const parseDate = (value) => {
  if (!value) return null;
  const s = String(value);
  return new Date(/[zZ]|[+-]\d\d:\d\d$/.test(s) ? s : `${s}Z`);
};

export const fmtRelative = (value) => {
  const d = parseDate(value);
  if (!d) return "—";
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return "hace un momento";
  if (diff < 3600) return `hace ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `hace ${Math.floor(diff / 3600)} h`;
  if (diff < 86400 * 7) return `hace ${Math.floor(diff / 86400)} d`;
  return d.toLocaleDateString("es-PE", { day: "numeric", month: "short" });
};

export const fmtDay = (iso) => {
  const d = new Date(`${iso}T12:00:00`);
  return d.toLocaleDateString("es-PE", { day: "numeric", month: "short" });
};

export const initials = (name = "") =>
  name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0])
    .join("")
    .toUpperCase();

export const ROLE_LABEL = { admin: "Administrador", developer: "Desarrollador", viewer: "Usuario" };

export const greeting = () => {
  const h = new Date().getHours();
  if (h < 12) return "Buenos días";
  if (h < 19) return "Buenas tardes";
  return "Buenas noches";
};

import { initials } from "../lib/format";

const SIZES = { xs: "h-6 w-6 text-[10px]", sm: "h-7 w-7 text-[11px]", md: "h-9 w-9 text-[12.5px]", lg: "h-11 w-11 text-sm" };
const ROLE_TONE = {
  admin: "bg-ink-950 text-white",
  developer: "bg-accent text-white",
  viewer: "bg-mist-200 text-ink-800",
};

export default function Avatar({ name, role, size = "md" }) {
  return (
    <span
      className={`grid shrink-0 place-items-center rounded-full font-semibold tracking-wide ${SIZES[size]} ${
        ROLE_TONE[role] || ROLE_TONE.viewer
      }`}
    >
      {initials(name)}
    </span>
  );
}

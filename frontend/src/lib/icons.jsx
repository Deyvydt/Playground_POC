import {
  Bot, Wrench, ChartColumn, FileText, GraduationCap, Compass, MessageSquare, Search, Scale, Package,
  ShieldCheck, Code2, Users, Briefcase, Headset, Landmark, Receipt, Megaphone, Lightbulb, Brain, Truck,
  Building2, HeartPulse, Database,
} from "lucide-react";

export const AGENT_ICONS = {
  bot: Bot,
  brain: Brain,
  wrench: Wrench,
  headset: Headset,
  "chart-column": ChartColumn,
  "file-text": FileText,
  "graduation-cap": GraduationCap,
  users: Users,
  scale: Scale,
  "shield-check": ShieldCheck,
  code: Code2,
  database: Database,
  briefcase: Briefcase,
  landmark: Landmark,
  receipt: Receipt,
  megaphone: Megaphone,
  lightbulb: Lightbulb,
  search: Search,
  compass: Compass,
  "message-square": MessageSquare,
  package: Package,
  truck: Truck,
  building: Building2,
  "heart-pulse": HeartPulse,
};

const SIZES = {
  sm: "h-7 w-7 rounded-md",
  md: "h-9 w-9 rounded-lg",
  lg: "h-11 w-11 rounded-xl",
  xl: "h-14 w-14 rounded-2xl",
};
const ICON_SIZES = { sm: 14, md: 17, lg: 20, xl: 24 };

export function AgentIcon({ name, size = "md", tone = "light", className = "" }) {
  const Icon = AGENT_ICONS[name] || Bot;
  const tones = {
    light: "bg-mist-100 text-ink-950 ring-1 ring-inset ring-mist-200",
    dark: "bg-ink-950 text-white",
    accent: "bg-accent-50 text-accent-dark ring-1 ring-inset ring-accent-100",
  };
  return (
    <span className={`grid shrink-0 place-items-center ${SIZES[size]} ${tones[tone]} ${className}`}>
      <Icon size={ICON_SIZES[size]} strokeWidth={1.75} />
    </span>
  );
}

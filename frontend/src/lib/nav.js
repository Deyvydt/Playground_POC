import { House, Bot, Workflow, Coins, Users, Settings } from "lucide-react";

export const NAV_ITEMS = [
  { to: "/", label: "Inicio", icon: House, end: true, hint: "Vista general de tu espacio" },
  { to: "/agentes", label: "Agentes", icon: Bot, hint: "Crea, prueba y administra agentes" },
  { to: "/flujos", label: "Flujos", icon: Workflow, hint: "Encadena agentes en un flujo de trabajo" },
  { to: "/consumo", label: "Consumo", icon: Coins, permission: "metrics", hint: "Tokens, costos y rendimiento" },
  { to: "/usuarios", label: "Usuarios", icon: Users, permission: "manage_users", hint: "Cuentas y roles de acceso" },
  { to: "/configuracion", label: "Configuración", icon: Settings, hint: "Modelos, herramientas y permisos" },
];

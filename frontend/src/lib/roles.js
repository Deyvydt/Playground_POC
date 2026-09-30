export const ROLES = [
  { id: "admin", label: "Administrador", desc: "Acceso total, incluida la gestión de usuarios." },
  { id: "developer", label: "Desarrollador", desc: "Crea, edita y prueba agentes y su conocimiento." },
  { id: "viewer", label: "Usuario", desc: "Conversa con los agentes disponibles." },
];

export const PERMISSION_LABELS = [
  { id: "chat", label: "Conversar con agentes" },
  { id: "create", label: "Crear agentes" },
  { id: "edit", label: "Editar y pausar agentes" },
  { id: "knowledge", label: "Gestionar conocimiento" },
  { id: "metrics", label: "Ver consumo y métricas" },
  { id: "delete", label: "Eliminar agentes" },
  { id: "manage_users", label: "Gestionar usuarios" },
];

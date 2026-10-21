import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Loader2, Pencil, Plus, Search, Trash2, UserCheck, UserX } from "lucide-react";
import PageHeader from "../components/PageHeader";
import Avatar from "../components/Avatar";
import Badge from "../components/Badge";
import Modal from "../components/Modal";
import Tooltip from "../components/Tooltip";
import { createUser, deleteUser, errorMessage, listUsers, updateUser } from "../api/client";
import { useSession } from "../context/SessionContext";
import { useUI } from "../context/UIContext";
import { ROLES } from "../lib/roles";
import { fmtRelative } from "../lib/format";

const ROLE_TONE = { admin: "dark", developer: "accent", viewer: "neutral" };
const EMPTY = { name: "", email: "", title: "", role: "viewer", password: "" };

function UserForm({ open, initial, onClose, onSaved }) {
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (open) {
      setForm(initial ? { ...EMPTY, ...initial, password: "" } : EMPTY);
      setError("");
    }
  }, [open, initial]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = { name: form.name, email: form.email, title: form.title, role: form.role };
      if (form.password) payload.password = form.password;
      const saved = initial ? await updateUser(initial.id, payload) : await createUser(payload);
      onSaved(saved, Boolean(initial));
    } catch (err) {
      setError(errorMessage(err, "No se pudo guardar el usuario"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title={initial ? "Editar usuario" : "Nuevo usuario"} subtitle={initial ? initial.email : "Crea una cuenta y asigna su rol."}>
      <form onSubmit={submit} className="space-y-4 px-6 py-5">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="u-name">Nombre completo</label>
            <input id="u-name" required minLength={2} value={form.name} onChange={set("name")} className="input" />
          </div>
          <div>
            <label className="label" htmlFor="u-title">Cargo</label>
            <input id="u-title" value={form.title} onChange={set("title")} placeholder="Ej. Project Manager" className="input" />
          </div>
        </div>
        <div>
          <label className="label" htmlFor="u-email">Correo</label>
          <input id="u-email" type="email" required value={form.email} onChange={set("email")} placeholder="nombre@tcs.com" className="input" />
        </div>
        <div>
          <span className="label">Rol</span>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            {ROLES.map((r) => (
              <button
                type="button"
                key={r.id}
                onClick={() => setForm((f) => ({ ...f, role: r.id }))}
                className={`focus-ring rounded-lg border p-3 text-left transition ${form.role === r.id ? "border-ink-950 bg-mist-50 ring-1 ring-ink-950" : "border-mist-200 hover:border-mist-300"}`}
              >
                <span className="block text-[13px] font-medium text-ink-950">{r.label}</span>
                <span className="mt-0.5 block text-[11.5px] leading-snug text-mist-500">{r.desc}</span>
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="label" htmlFor="u-pass">{initial ? "Nueva contraseña" : "Contraseña temporal"}</label>
          <input
            id="u-pass"
            type="password"
            required={!initial}
            minLength={6}
            value={form.password}
            onChange={set("password")}
            placeholder={initial ? "Déjala vacía para mantener la actual" : "Mínimo 6 caracteres"}
            className="input"
            autoComplete="new-password"
          />
        </div>
        {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-[12.5px] text-red-700">{error}</p>}
        <div className="-mx-6 -mb-5 flex justify-end gap-2 border-t border-mist-100 bg-mist-50/60 px-6 py-4">
          <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
          <button type="submit" disabled={saving} className="btn-primary">
            {saving && <Loader2 size={14} className="animate-spin" />}
            {initial ? "Guardar cambios" : "Crear usuario"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default function UsersPage() {
  const { currentUser, setCurrentUser } = useSession();
  const { toast, confirm } = useUI();
  const [users, setUsers] = useState([]);
  const [query, setQuery] = useState("");
  const [formState, setFormState] = useState({ open: false, user: null });

  const load = () => listUsers().then(setUsers).catch(() => {});
  useEffect(() => {
    load();
  }, []);

  const q = query.trim().toLowerCase();
  const visible = users.filter((u) => !q || u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q));

  const onSaved = (saved, edited) => {
    toast(edited ? "Usuario actualizado" : `Cuenta creada para ${saved.name}`);
    if (saved.id === currentUser.id) setCurrentUser(saved);
    setFormState({ open: false, user: null });
    load();
  };

  const toggleActive = async (u) => {
    try {
      await updateUser(u.id, { is_active: !u.is_active });
      toast(u.is_active ? `${u.name} fue desactivado` : `${u.name} fue reactivado`, "info");
      load();
    } catch (err) {
      toast(errorMessage(err), "error");
    }
  };

  const remove = async (u) => {
    const ok = await confirm({ title: `¿Eliminar a ${u.name}?`, description: "La cuenta dejará de tener acceso. Esta acción no se puede deshacer.", confirmLabel: "Eliminar", danger: true });
    if (!ok) return;
    try {
      await deleteUser(u.id);
      toast("Usuario eliminado");
      load();
    } catch (err) {
      toast(errorMessage(err), "error");
    }
  };

  return (
    <div>
      <PageHeader
        title="Usuarios"
        description="Cuentas y roles de acceso"
        actions={
          <button onClick={() => setFormState({ open: true, user: null })} className="btn-primary">
            <Plus size={15} /> Nuevo usuario
          </button>
        }
      />
      <div className="mx-auto max-w-[1200px] px-8 py-8">
        <div className="mb-5 grid grid-cols-2 gap-3 md:grid-cols-4">
          {[{ id: "all", label: "Total" }, ...ROLES].map((r, i) => (
            <motion.div key={r.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }} className="card px-4 py-3">
              <p className="text-[12px] text-mist-500">{r.id === "all" ? "Total" : r.label + (r.id === "viewer" ? "s" : "es")}</p>
              <p className="mt-1 text-[22px] font-semibold tabular text-ink-950">
                {r.id === "all" ? users.length : users.filter((u) => u.role === r.id).length}
              </p>
            </motion.div>
          ))}
        </div>

        <div className="card overflow-hidden">
          <div className="border-b border-mist-100 p-3">
            <div className="relative w-full sm:w-72">
              <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-mist-400" />
              <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar por nombre o correo…" className="input pl-9" />
            </div>
          </div>
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-mist-100 bg-mist-50/60 text-left text-[11.5px] text-mist-500">
                <th className="py-2.5 pl-5 pr-4 font-medium">Usuario</th>
                <th className="px-4 font-medium">Rol</th>
                <th className="hidden px-4 font-medium md:table-cell">Estado</th>
                <th className="hidden px-4 font-medium lg:table-cell">Último acceso</th>
                <th className="w-32 px-4" />
              </tr>
            </thead>
            <tbody className="divide-y divide-mist-100">
              {visible.map((u, i) => {
                const self = u.id === currentUser.id;
                return (
                  <motion.tr key={u.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }} className="group hover:bg-mist-50/60">
                    <td className="py-3 pl-5 pr-4">
                      <div className={`flex items-center gap-3 ${u.is_active ? "" : "opacity-50"}`}>
                        <Avatar name={u.name} role={u.role} size="md" />
                        <div className="min-w-0">
                          <p className="truncate font-medium text-ink-950">
                            {u.name} {self && <span className="text-[11.5px] font-normal text-mist-400">(tú)</span>}
                          </p>
                          <p className="truncate text-[12px] text-mist-500">{u.email}{u.title && ` · ${u.title}`}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4"><Badge tone={ROLE_TONE[u.role]}>{ROLES.find((r) => r.id === u.role)?.label}</Badge></td>
                    <td className="hidden px-4 md:table-cell">
                      {u.is_active ? <Badge tone="good" dot>Activo</Badge> : <Badge dot>Inactivo</Badge>}
                    </td>
                    <td className="hidden px-4 text-mist-500 lg:table-cell">{u.last_login_at ? fmtRelative(u.last_login_at) : "Nunca"}</td>
                    <td className="px-4">
                      <div className="flex justify-end gap-0.5">
                        <Tooltip label="Editar">
                          <button onClick={() => setFormState({ open: true, user: u })} className="btn-icon"><Pencil size={14} /></button>
                        </Tooltip>
                        {!self && (
                          <>
                            <Tooltip label={u.is_active ? "Desactivar acceso" : "Reactivar acceso"}>
                              <button onClick={() => toggleActive(u)} className="btn-icon">{u.is_active ? <UserX size={14} /> : <UserCheck size={14} />}</button>
                            </Tooltip>
                            <Tooltip label="Eliminar">
                              <button onClick={() => remove(u)} className="btn-icon hover:bg-red-50 hover:text-red-600"><Trash2 size={14} /></button>
                            </Tooltip>
                          </>
                        )}
                      </div>
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <UserForm open={formState.open} initial={formState.user} onClose={() => setFormState({ open: false, user: null })} onSaved={onSaved} />
    </div>
  );
}

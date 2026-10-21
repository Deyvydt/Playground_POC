import { createContext, useCallback, useContext, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CircleCheck, CircleAlert, Info, X } from "lucide-react";
import Modal from "../components/Modal";

const UIContext = createContext(null);

const TOAST_ICON = { success: CircleCheck, error: CircleAlert, info: Info };
const TOAST_TONE = { success: "text-emerald-600", error: "text-red-600", info: "text-accent" };

export function UIProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const [confirmState, setConfirmState] = useState(null);
  const resolver = useRef(null);

  const toast = useCallback((message, type = "success") => {
    const id = Math.random().toString(36).slice(2);
    setToasts((t) => [...t, { id, message, type }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4200);
  }, []);

  const confirm = useCallback((options) => {
    setConfirmState(options);
    return new Promise((resolve) => {
      resolver.current = resolve;
    });
  }, []);

  const closeConfirm = (value) => {
    resolver.current?.(value);
    setConfirmState(null);
  };

  return (
    <UIContext.Provider value={{ toast, confirm }}>
      {children}

      <div className="pointer-events-none fixed bottom-5 right-5 z-[80] flex w-80 flex-col gap-2">
        <AnimatePresence>
          {toasts.map((t) => {
            const Icon = TOAST_ICON[t.type];
            return (
              <motion.div
                key={t.id}
                layout
                initial={{ opacity: 0, y: 12, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, x: 24 }}
                transition={{ type: "spring", stiffness: 400, damping: 32 }}
                className="pointer-events-auto flex items-start gap-2.5 rounded-xl border border-mist-200 bg-white px-3.5 py-3 shadow-pop"
              >
                <Icon size={16} className={`mt-0.5 shrink-0 ${TOAST_TONE[t.type]}`} />
                <p className="flex-1 text-[13px] leading-snug text-ink-950">{t.message}</p>
                <button
                  onClick={() => setToasts((all) => all.filter((x) => x.id !== t.id))}
                  className="text-mist-400 hover:text-ink-950"
                  aria-label="Cerrar notificación"
                >
                  <X size={14} />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      <Modal open={Boolean(confirmState)} onClose={() => closeConfirm(false)} size="sm">
        {confirmState && (
          <div className="p-6">
            <h3 className="text-[15px] font-semibold text-ink-950">{confirmState.title}</h3>
            {confirmState.description && (
              <p className="mt-1.5 text-[13px] leading-relaxed text-mist-500">{confirmState.description}</p>
            )}
            <div className="mt-6 flex justify-end gap-2">
              <button className="btn-secondary" onClick={() => closeConfirm(false)}>
                Cancelar
              </button>
              <button
                autoFocus
                className={confirmState.danger ? "btn bg-red-600 px-4 py-2 text-white hover:bg-red-700" : "btn-primary"}
                onClick={() => closeConfirm(true)}
              >
                {confirmState.confirmLabel || "Confirmar"}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </UIContext.Provider>
  );
}

export const useUI = () => useContext(UIContext);

import { useEffect } from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";

const WIDTHS = { sm: "max-w-sm", md: "max-w-lg", lg: "max-w-2xl" };

export default function Modal({ open, onClose, title, subtitle, size = "md", children }) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[60] flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="absolute inset-0 bg-ink-950/30 backdrop-blur-[3px]" onClick={onClose} />
          <motion.div
            role="dialog"
            aria-modal="true"
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
            transition={{ type: "spring", stiffness: 420, damping: 34 }}
            className={`relative flex max-h-[90vh] w-full ${WIDTHS[size]} flex-col overflow-hidden rounded-2xl border border-mist-200 bg-white shadow-pop`}
          >
            {title && (
              <div className="flex items-start justify-between border-b border-mist-100 px-6 py-4">
                <div>
                  <h2 className="text-[15px] font-semibold text-ink-950">{title}</h2>
                  {subtitle && <p className="mt-0.5 text-[12.5px] text-mist-500">{subtitle}</p>}
                </div>
                <button onClick={onClose} className="btn-icon -mr-2" aria-label="Cerrar">
                  <X size={16} />
                </button>
              </div>
            )}
            <div className="overflow-y-auto">{children}</div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body
  );
}

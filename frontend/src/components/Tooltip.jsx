import { cloneElement, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "framer-motion";

// Se renderiza en un portal con posición fija para no quedar recortado por contenedores con overflow.
export default function Tooltip({ label, side = "top", shortcut, disabled = false, children }) {
  const [pos, setPos] = useState(null);
  const timer = useRef(null);

  if (!label || disabled) return children;

  const show = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setPos(rect), 280);
  };
  const hide = () => {
    clearTimeout(timer.current);
    setPos(null);
  };

  const placement = pos && {
    top: { left: pos.left + pos.width / 2, top: pos.top - 8, transform: "translate(-50%, -100%)" },
    bottom: { left: pos.left + pos.width / 2, top: pos.bottom + 8, transform: "translateX(-50%)" },
    right: { left: pos.right + 10, top: pos.top + pos.height / 2, transform: "translateY(-50%)" },
    left: { left: pos.left - 10, top: pos.top + pos.height / 2, transform: "translate(-100%, -50%)" },
  }[side];

  return (
    <>
      {cloneElement(children, {
        onMouseEnter: show,
        onMouseLeave: hide,
        onFocus: show,
        onBlur: hide,
        onMouseDown: hide,
        "aria-label": children.props["aria-label"] || label,
      })}
      {createPortal(
        <AnimatePresence>
          {pos && (
            <div className="pointer-events-none fixed z-[90]" style={placement}>
              <motion.div
                initial={{ opacity: 0, scale: 0.94 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.12 }}
                className="flex items-center gap-2 whitespace-nowrap rounded-md bg-ink-950 px-2 py-1 text-[11.5px] font-medium text-white shadow-pop"
              >
                {label}
                {shortcut && (
                  <kbd className="rounded bg-white/15 px-1 font-mono text-[10px] text-white/80">{shortcut}</kbd>
                )}
              </motion.div>
            </div>
          )}
        </AnimatePresence>,
        document.body
      )}
    </>
  );
}

import { useEffect, useRef, useState } from "react";

export default function AnimatedNumber({ value, format = (n) => n, duration = 900 }) {
  const [display, setDisplay] = useState(0);
  const from = useRef(0);

  useEffect(() => {
    if (typeof value !== "number") return;
    const start = performance.now();
    const initial = from.current;
    let frame;
    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(initial + (value - initial) * eased);
      if (t < 1) frame = requestAnimationFrame(tick);
      else from.current = value;
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, duration]);

  if (typeof value !== "number") return <span>—</span>;
  return <span className="tabular">{format(display)}</span>;
}

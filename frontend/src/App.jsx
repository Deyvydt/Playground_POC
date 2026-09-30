import { useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import Sidebar from "./components/Sidebar";
import CommandPalette from "./components/CommandPalette";
import Login from "./pages/Login";
import Home from "./pages/Home";
import Agents from "./pages/Agents";
import AgentDetail from "./pages/AgentDetail";
import Flows from "./pages/Flows";
import Usage from "./pages/Usage";
import UsersPage from "./pages/UsersPage";
import SettingsPage from "./pages/SettingsPage";
import { useSession } from "./context/SessionContext";

const readCollapsed = () => {
  try {
    return localStorage.getItem("ap-sidebar-collapsed") === "1";
  } catch {
    return false;
  }
};

function Guard({ permission, children }) {
  const { can } = useSession();
  return can(permission) ? children : <Navigate to="/" replace />;
}

function Shell() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(readCollapsed);
  const [paletteOpen, setPaletteOpen] = useState(false);

  useEffect(() => {
    try {
      localStorage.setItem("ap-sidebar-collapsed", collapsed ? "1" : "0");
    } catch {
      /* almacenamiento no disponible */
    }
  }, [collapsed]);

  useEffect(() => {
    const onKey = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "b") {
        e.preventDefault();
        setCollapsed((v) => !v);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="flex h-screen w-full overflow-hidden bg-mist-50"
    >
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((v) => !v)} onOpenPalette={() => setPaletteOpen(true)} />
      <main className="relative flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname.split("/").slice(0, 3).join("/")}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className="min-h-full"
          >
            <Routes location={location}>
              <Route path="/" element={<Home />} />
              <Route path="/agentes" element={<Agents />} />
              <Route path="/agentes/:agentId" element={<AgentDetail />} />
              <Route path="/flujos" element={<Flows />} />
              <Route path="/consumo" element={<Guard permission="metrics"><Usage /></Guard>} />
              <Route path="/usuarios" element={<Guard permission="manage_users"><UsersPage /></Guard>} />
              <Route path="/configuracion" element={<SettingsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </motion.div>
        </AnimatePresence>
      </main>
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
    </motion.div>
  );
}

function Splash() {
  return (
    <div className="grid h-screen place-items-center bg-mist-50">
      <motion.img
        src="/tcs-mark.svg"
        alt=""
        className="h-10"
        animate={{ opacity: [0.3, 1, 0.3] }}
        transition={{ duration: 1.6, repeat: Infinity }}
      />
    </div>
  );
}

export default function App() {
  const { status } = useSession();
  if (status === "checking") return <Splash />;

  return (
    <AnimatePresence mode="wait">
      {status === "authenticated" ? <Shell key="shell" /> : <Login key="login" />}
    </AnimatePresence>
  );
}

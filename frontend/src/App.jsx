import { Routes, Route } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import Sidebar from "./components/Sidebar";
import Login from "./pages/Login";
import Overview from "./pages/Overview";
import Dashboard from "./pages/Dashboard";
import Agents from "./pages/Agents";
import AgentDetail from "./pages/AgentDetail";
import MultiAgentFlow from "./pages/MultiAgentFlow";
import SettingsPage from "./pages/SettingsPage";
import { useSession } from "./context/SessionContext";

function Shell() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.99 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.45, ease: "easeOut" }}
      className="flex h-screen w-full overflow-hidden bg-mist-50"
    >
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/panel" element={<Dashboard />} />
          <Route path="/agentes" element={<Agents />} />
          <Route path="/agentes/:agentId" element={<AgentDetail />} />
          <Route path="/flujo" element={<MultiAgentFlow />} />
          <Route path="/configuracion" element={<SettingsPage />} />
        </Routes>
      </main>
    </motion.div>
  );
}

export default function App() {
  const { isAuthenticated } = useSession();

  return (
    <AnimatePresence mode="wait">
      {isAuthenticated ? <Shell key="shell" /> : <Login key="login" />}
    </AnimatePresence>
  );
}

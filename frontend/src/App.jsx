import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Overview from "./pages/Overview";
import Dashboard from "./pages/Dashboard";
import Agents from "./pages/Agents";
import AgentDetail from "./pages/AgentDetail";
import MultiAgentFlow from "./pages/MultiAgentFlow";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-mist-50">
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
    </div>
  );
}

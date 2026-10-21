import axios from "axios";

export const TOKEN_KEY = "ap-token";

export const getToken = () => localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);

const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401 && !error.config.url.includes("/auth/login")) {
      window.dispatchEvent(new Event("auth:expired"));
    }
    return Promise.reject(error);
  }
);

export const errorMessage = (err, fallback = "Ocurrió un error inesperado") =>
  err?.response?.data?.detail && typeof err.response.data.detail === "string"
    ? err.response.data.detail
    : fallback;

export const login = (email, password) => api.post("/auth/login", { email, password }).then((r) => r.data);
export const me = () => api.get("/auth/me").then((r) => r.data);

export const health = () => api.get("/health").then((r) => r.data);
export const listModels = () => api.get("/models").then((r) => r.data);
export const listTools = () => api.get("/tools").then((r) => r.data);

export const listUsers = () => api.get("/users").then((r) => r.data);
export const createUser = (payload) => api.post("/users", payload).then((r) => r.data);
export const updateUser = (id, payload) => api.put(`/users/${id}`, payload).then((r) => r.data);
export const deleteUser = (id) => api.delete(`/users/${id}`).then((r) => r.data);

export const listAgents = () => api.get("/agents").then((r) => r.data);
export const getAgent = (id) => api.get(`/agents/${id}`).then((r) => r.data);
export const createAgent = (payload) => api.post("/agents", payload).then((r) => r.data);
export const updateAgent = (id, payload) => api.put(`/agents/${id}`, payload).then((r) => r.data);
export const deleteAgent = (id) => api.delete(`/agents/${id}`).then((r) => r.data);

export const listKnowledge = (agentId) => api.get(`/agents/${agentId}/knowledge`).then((r) => r.data);
export const uploadKnowledge = (agentId, file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post(`/agents/${agentId}/knowledge`, form).then((r) => r.data);
};
export const deleteKnowledge = (docId) => api.delete(`/agents/knowledge/${docId}`).then((r) => r.data);

export const listConversations = (agentId) => api.get(`/agents/${agentId}/conversations`).then((r) => r.data);
export const listMessages = (conversationId) => api.get(`/conversations/${conversationId}/messages`).then((r) => r.data);
export const deleteConversation = (conversationId) => api.delete(`/conversations/${conversationId}`).then((r) => r.data);
export const sendMessage = (agentId, payload) => api.post(`/agents/${agentId}/chat`, payload).then((r) => r.data);

// Emite cada evento NDJSON del backend a medida que llega.
export async function streamOrchestration(payload, onEvent) {
  const res = await fetch("/api/orchestration/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "No se pudo ejecutar el flujo");
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop();
    lines.filter(Boolean).forEach((line) => onEvent(JSON.parse(line)));
  }
}

export const metricsSummary = (days = 30) => api.get("/metrics/summary", { params: { days } }).then((r) => r.data);
export const metricsTimeseries = (days = 14, agentId) =>
  api.get("/metrics/timeseries", { params: { days, agent_id: agentId } }).then((r) => r.data);
export const metricsActivity = (limit = 8) => api.get("/metrics/activity", { params: { limit } }).then((r) => r.data);

// Servicios de gobierno (governance :8100) y laboratorio (agent-lab :8200): validan el mismo token de sesión.
const withSession = (instance) => {
  instance.interceptors.request.use((config) => {
    const token = getToken();
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  });
  return instance;
};
const gov = withSession(axios.create({ baseURL: "/gov" }));
const lab = withSession(axios.create({ baseURL: "/lab" }));

export const govHealth = () => gov.get("/health", { timeout: 5000 }).then((r) => r.data);
export const govAreas = () => gov.get("/areas").then((r) => r.data);
export const govSistemas = () => gov.get("/sistemas").then((r) => r.data);
export const govCreateSistema = (payload) => gov.post("/sistemas", payload).then((r) => r.data);
export const govAgents = (params) => gov.get("/agents", { params }).then((r) => r.data);
export const govAgent = (id) => gov.get(`/agents/${id}`).then((r) => r.data);
export const govAgentActivity = (id, minutes = 1440) =>
  gov.get(`/agents/${id}/activity`, { params: { minutes } }).then((r) => r.data);
export const govRegisterAgent = (payload) => gov.post("/agents", payload).then((r) => r.data);
export const govUpdateAgent = (id, payload) => gov.patch(`/agents/${id}`, payload).then((r) => r.data);
export const govPauseAgent = (id, reason) => gov.post(`/agents/${id}/pause`, { reason }).then((r) => r.data);
export const govResumeAgent = (id) => gov.post(`/agents/${id}/resume`).then((r) => r.data);
export const govDeleteAgent = (id) => gov.delete(`/agents/${id}`);
export const govRegenerateKey = (id) => gov.post(`/agents/${id}/regenerate-key`).then((r) => r.data);
export const govNotifications = (limit = 30) => gov.get("/notifications", { params: { limit } }).then((r) => r.data);
export const govMarkRead = (id) => gov.post(`/notifications/${id}/read`).then((r) => r.data);
export const govMarkAllRead = () => gov.post("/notifications/read-all").then((r) => r.data);

export const labRun = (sistema, payload) => lab.post(`/runs/${sistema}`, payload).then((r) => r.data);

export default api;

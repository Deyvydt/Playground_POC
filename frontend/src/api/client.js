import axios from "axios";

const api = axios.create({ baseURL: "/api" });

export const health = () => api.get("/health").then((r) => r.data);
export const listModels = () => api.get("/models").then((r) => r.data);
export const listTools = () => api.get("/tools").then((r) => r.data);
export const listUsers = () => api.get("/users").then((r) => r.data);

export const listAgents = () => api.get("/agents").then((r) => r.data);
export const getAgent = (id) => api.get(`/agents/${id}`).then((r) => r.data);
export const createAgent = (payload) => api.post("/agents", payload).then((r) => r.data);
export const updateAgent = (id, payload) => api.put(`/agents/${id}`, payload).then((r) => r.data);
export const deleteAgent = (id) => api.delete(`/agents/${id}`).then((r) => r.data);

export const listKnowledge = (agentId) => api.get(`/agents/${agentId}/knowledge`).then((r) => r.data);
export const uploadKnowledge = (agentId, file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post(`/agents/${agentId}/knowledge`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);
};
export const deleteKnowledge = (docId) => api.delete(`/agents/knowledge/${docId}`).then((r) => r.data);

export const listConversations = (agentId) => api.get(`/agents/${agentId}/conversations`).then((r) => r.data);
export const listMessages = (conversationId) => api.get(`/conversations/${conversationId}/messages`).then((r) => r.data);
export const sendMessage = (agentId, payload) => api.post(`/agents/${agentId}/chat`, payload).then((r) => r.data);

export const runOrchestration = (payload) => api.post("/orchestration/run", payload).then((r) => r.data);

export const metricsSummary = () => api.get("/metrics/summary").then((r) => r.data);
export const metricsTimeseries = () => api.get("/metrics/timeseries").then((r) => r.data);

export default api;

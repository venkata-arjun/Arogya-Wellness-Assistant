import { api } from "./client";

export const sendWellnessMessage = async (userId, message) => {
  const payload = { user_id: userId, message };
  const res = await api.post("/api/wellness", payload);
  return res.data;
};

export const getMemoryHistory = async (userId) => {
  const res = await api.get(`/api/history/${userId}`);
  return res.data;
};

export const getDbHistory = async (userId) => {
  const res = await api.get(`/api/db-history/${userId}`);
  return res.data;
};

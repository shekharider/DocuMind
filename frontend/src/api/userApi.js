import api from "../services/axios";

export const getCurrentUser = async () => {
  const response = await api.get("/auth/me");

  return response.data;
};
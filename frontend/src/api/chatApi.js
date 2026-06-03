import api from "../services/axios";

export const getSessions = async () => {
  const response = await api.get(
    "/chat/sessions"
  );

  return response.data;
};

export const createSession =
  async (title) => {

    const response = await api.post(
      "/chat/sessions",
      {
        title,
      }
    );

    return response.data;
};
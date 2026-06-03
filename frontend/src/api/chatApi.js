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

export const getMessages = async (sessionId) => {
  const response = await api.get(
    `/chat/messages/${sessionId}`
  );

  return response.data;
};

export const askQuestion = async (
  sessionId,
  question
) => {
  const response = await api.post(
    "/chat/ask",
    null,
    {
      params: {
        session_id: sessionId,
        question: question,
      },
    }
  );

  return response.data;
};

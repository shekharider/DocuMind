import api from "../services/axios";

export const getSessionDocuments = async (sessionId) => {
  const response = await api.get(
    `/documents/session/${sessionId}`
  );

  return response.data;
};

export const uploadDocument = async (
  sessionId,
  file
) => {
  const formData = new FormData();

  formData.append("session_id", sessionId);
  formData.append("file", file);

  const response = await api.post(
    "/documents/upload",
    formData
  );

  return response.data;
};

export const deleteDocument = async (
  documentId
) => {
  const response = await api.delete(
    `/documents/${documentId}`
  );

  return response.data;
};


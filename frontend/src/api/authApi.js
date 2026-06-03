import api from "../services/axios";

export const signupUser = async (userData) => {
  const response = await api.post(
    "/auth/signup",
    userData
  );

  return response.data;
};

export const loginUser = async (
  username,
  password
) => {
  const formData = new URLSearchParams();

  formData.append("username", username);
  formData.append("password", password);

  const response = await api.post(
    "/auth/login",
    formData,
    {
      headers: {
        "Content-Type":
          "application/x-www-form-urlencoded",
      },
    }
  );

  return response.data;
};

export const getMe = async () => {
  const response = await api.get("/auth/me");

  return response.data;
};
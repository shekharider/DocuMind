import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { loginUser } from "../api/authApi";

function Login() {
  const [username, setUsername] =
    useState("");

  const [password, setPassword] =
    useState("");

  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      const data = await loginUser(
        username,
        password
      );

      localStorage.setItem(
        "token",
        data.access_token
      );

      navigate("/dashboard");
    } catch (error) {
      console.error("Login error:", error);
      const message =
        error.response?.data?.detail ||
        error.message ||
        "Invalid credentials";
      alert(message);
    }
  };

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <form
        onSubmit={handleLogin}
        style={{
          width: "350px",
        }}
      >
        <h1>🧠 DocuMind</h1>

        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) =>
            setUsername(e.target.value)
          }
        />

        <br />
        <br />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) =>
            setPassword(e.target.value)
          }
        />

        <br />
        <br />

        <button type="submit">
          Login
        </button>
      </form>
    </div>
  );
}

export default Login;
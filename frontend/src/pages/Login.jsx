import { useState } from "react";
import { useNavigate } from "react-router-dom";

import "./../components/AuthCard.css";

import { loginUser } from "../api/authApi";

function Login() {
  const locationState = (typeof window !== "undefined" && window.history && window.history.state) ? window.history.state : null;
  const successFromSignup = locationState?.success || "";
  const [username, setUsername] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();

    setError("");
    setLoading(true);

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
    } catch (err) {
      console.error("Login error:", err);
      const message =
        err.response?.data?.detail ||
        err.message ||
        "Invalid credentials";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="auth-logo-mark">🧠</div>
          <div>
            <h1 className="auth-title">DocuMind</h1>
            <div className="auth-subtitle">
              Welcome back to your document assistant
            </div>
          </div>
        </div>

        <div className="auth-subtitle" style={{ marginTop: 0 }}>
          Chat with your documents using AI-powered search.
        </div>

        <form
          onSubmit={handleLogin}
          className="auth-fields"
        >
          <div className="auth-field">
            <div className="auth-label">Username</div>
            <input
              className="auth-input"
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) =>
                setUsername(e.target.value)
              }
              autoComplete="username"
              disabled={loading}
              required
            />
          </div>

          <div className="auth-field">
            <div className="auth-label">Password</div>
            <input
              className="auth-input"
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) =>
                setPassword(e.target.value)
              }
              autoComplete="current-password"
              disabled={loading}
              required
            />
          </div>

          <div className="auth-actions">
            <button
              className="auth-button"
              type="submit"
              disabled={loading}
            >
              {loading ? "Logging in..." : "Login"}
            </button>
          </div>

          {error && (
            <div className="auth-error">{error}</div>
          )}

          {!error && successFromSignup && (
            <div className="auth-success">
              {successFromSignup}
            </div>
          )}

          <div className="auth-switch">
            Don&apos;t have an account?{" "}
            <span
              className="auth-link"
              role="button"
              tabIndex={0}
              onClick={() => navigate("/signup")}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  navigate("/signup");
                }
              }}
            >
              Create Account
            </span>
          </div>
        </form>
      </div>
    </div>
  );
}

export default Login;


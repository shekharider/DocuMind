import { useState } from "react";
import { useNavigate } from "react-router-dom";

import "./../components/AuthCard.css";

import { signupUser } from "../api/authApi";

function Signup() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

  const navigate = useNavigate();

  const validate = () => {
    const errs = {};

    if (!username.trim()) errs.username = "Username is required";
    if (!email.trim()) errs.email = "Email is required";
    if (!password) errs.password = "Password is required";
    if (!confirmPassword) errs.confirmPassword = "Confirm Password is required";
    if (password && confirmPassword && password !== confirmPassword) {
      errs.confirmPassword = "Passwords must match";
    }

    return errs;
  };

  const handleSignup = async (e) => {
    e.preventDefault();

    const errs = validate();
    setFieldErrors(errs);

    if (Object.keys(errs).length > 0) {
      setError("");
      return;
    }

    setLoading(true);
    setError("");

    try {
      await signupUser({
        username,
        email,
        password,
      });

      // Preferred UX: navigate to login with success message
      navigate("/login", {
        state: {
          success:
            "Account created successfully. Please login.",
        },
      });
    } catch (err) {
      console.error("Signup error:", err);
      const message =
        err.response?.data?.detail ||
        err.message ||
        "Failed to create account";
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
              Welcome to your document assistant
            </div>
          </div>
        </div>

        <form
          onSubmit={handleSignup}
          className="auth-fields"
        >
          <div className="auth-field">
            <div className="auth-label">Username</div>
            <input
              className="auth-input"
              type="text"
              value={username}
              onChange={(e) =>
                setUsername(e.target.value)
              }
              disabled={loading}
              required
            />
            {fieldErrors.username && (
              <div className="auth-error">{fieldErrors.username}</div>
            )}
          </div>

          <div className="auth-field">
            <div className="auth-label">Email</div>
            <input
              className="auth-input"
              type="email"
              value={email}
              onChange={(e) =>
                setEmail(e.target.value)
              }
              disabled={loading}
              required
            />
            {fieldErrors.email && (
              <div className="auth-error">{fieldErrors.email}</div>
            )}
          </div>

          <div className="auth-field">
            <div className="auth-label">Password</div>
            <input
              className="auth-input"
              type="password"
              value={password}
              onChange={(e) =>
                setPassword(e.target.value)
              }
              disabled={loading}
              required
            />
            {fieldErrors.password && (
              <div className="auth-error">{fieldErrors.password}</div>
            )}
          </div>

          <div className="auth-field">
            <div className="auth-label">Confirm Password</div>
            <input
              className="auth-input"
              type="password"
              value={confirmPassword}
              onChange={(e) =>
                setConfirmPassword(e.target.value)
              }
              disabled={loading}
              required
            />
            {fieldErrors.confirmPassword && (
              <div className="auth-error">{fieldErrors.confirmPassword}</div>
            )}
          </div>

          <div className="auth-actions">
            <button
              className="auth-button"
              type="submit"
              disabled={loading}
            >
              {loading ? "Creating Account..." : "Create Account"}
            </button>
          </div>

          {error && (
            <div className="auth-error">{error}</div>
          )}

          <div className="auth-switch">
            Already have an account?{" "}
            <span
              className="auth-link"
              role="button"
              tabIndex={0}
              onClick={() => navigate("/login")}
              onKeyDown={(e) => {
                if (e.key === "Enter") navigate("/login");
              }}
            >
              Login
            </span>
          </div>
        </form>
      </div>
    </div>
  );
}

export default Signup;


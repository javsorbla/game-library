import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import "../static/css/Auth.css";

export default function Register({ setAuthenticated }) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // create the user and log them in via session endpoint
      await axios.post("http://localhost:8000/api/register/", {
        username,
        email,
        password,
      });
      await axios.post("http://localhost:8000/api/login/", {
        username,
        password,
      });
      setError("");
      setAuthenticated(true);
      navigate("/dashboard");
    } catch (err) {
      setError("Unable to register user");
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <h2 className="auth-title">Create an account</h2>
        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Username
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </label>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <button type="submit" className="auth-button">
            Register
          </button>
        </form>
        {error && <p className="auth-error">{error}</p>}
        <p className="auth-footer">
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </div>
    </div>
  );
}

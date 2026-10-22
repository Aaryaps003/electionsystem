import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

export default function AdminLogin() {
  const { loggedIn, login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  if (loggedIn) return <Navigate to="/admin" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await login(username, password);
      navigate("/admin");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <form className="panel panel-title" style={{ maxWidth: 420, margin: "0 auto" }} onSubmit={submit}>
      <h2 className="page-title mb-3">Admin sign in</h2>
      <div className="mb-3">
        <label className="form-label" htmlFor="u">Username</label>
        <input id="u" className="form-control" value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
      </div>
      <div className="mb-3">
        <label className="form-label" htmlFor="p">Password</label>
        <input id="p" type="password" className="form-control" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </div>
      {error && <div className="alert alert-danger">{error}</div>}
      <button className="btn btn-primary w-100">Sign in</button>
    </form>
  );
}

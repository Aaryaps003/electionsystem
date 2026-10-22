import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

export default function Navbar() {
  const { loggedIn, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <nav className="topbar navbar navbar-expand">
      <div className="container">
        <Link to="/" className="brand-link">
          {/* Put your logo at frontend/public/images/mitwpu_logo.png — hidden if missing */}
          <img src="/images/mitwpu_logo.png" alt="" onError={(e) => (e.currentTarget.style.display = "none")} />
          <span className="brand-text">
            Smart College Election
            <small>MIT-WPU</small>
          </span>
        </Link>
        <div className="navbar-nav ms-auto align-items-center">
          <NavLink to="/vote" className="nav-link">Vote</NavLink>
          <NavLink to="/results" className="nav-link">Results</NavLink>
          {loggedIn ? (
            <>
              <NavLink to="/admin" className="nav-link">Admin</NavLink>
              <button className="btn btn-sm btn-outline-primary ms-2" onClick={() => { logout(); navigate("/"); }}>
                Log out
              </button>
            </>
          ) : (
            <NavLink to="/admin-login" className="nav-link">Admin</NavLink>
          )}
        </div>
      </div>
    </nav>
  );
}

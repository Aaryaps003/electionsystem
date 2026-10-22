import { useEffect } from "react";
import { Link } from "react-router-dom";

export default function Home() {
  // The home page uses the blue gradient background from the original design.
  useEffect(() => {
    document.body.classList.add("home-bg");
    return () => document.body.classList.remove("home-bg");
  }, []);

  return (
    <div className="d-flex justify-content-center py-3 py-md-5">
      <div className="hero-card">
        <img src="/images/mitwpu_logo.png" alt="MIT-WPU Logo" className="hero-logo mx-auto d-block"
          onError={(e) => (e.currentTarget.style.display = "none")} />
        <h3 className="hero-title">MIT-WPU Class Representative Election</h3>
        <p className="fs-5">Empowering digital democracy within our campus.</p>

        <div className="d-grid gap-3 col-10 mx-auto mt-3">
          <Link to="/vote" className="btn btn-vote btn-lg">Vote Now</Link>
          <Link to="/results" className="btn btn-main btn-lg">View Results</Link>
          <Link to="/admin-login" className="btn btn-admin btn-lg">Admin Login</Link>
        </div>

        <p className="mt-4 mb-0 text-muted">Developed by <b>Aarya Shinde</b> | MCA FY | MIT-WPU Pune</p>
      </div>
    </div>
  );
}

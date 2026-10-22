import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth.jsx";
import Navbar from "./components/Navbar.jsx";
import Home from "./pages/Home.jsx";
import Vote from "./pages/Vote.jsx";
import Results from "./pages/Results.jsx";
import AdminLogin from "./pages/AdminLogin.jsx";
import Admin from "./pages/Admin.jsx";

function RequireAdmin({ children }) {
  const { loggedIn } = useAuth();
  return loggedIn ? children : <Navigate to="/admin-login" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <Navbar />
      <main className="container py-4">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/vote" element={<Vote />} />
          <Route path="/results" element={<Results />} />
          <Route path="/admin-login" element={<AdminLogin />} />
          <Route path="/admin" element={<RequireAdmin><Admin /></RequireAdmin>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <footer className="site-footer">
        <div className="container">MIT World Peace University · Student election portal</div>
      </footer>
    </AuthProvider>
  );
}

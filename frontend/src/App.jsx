import { BrowserRouter, Routes, Route, Link, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import VoterDashboard from './pages/VoterDashboard'
import ElectionDetails from './pages/ElectionDetails'
import AuditDashboard from './pages/AuditDashboard'
import './App.css'

function Home() {
  const { user, logout } = useAuth()

  const dashboardRoutes = {
    VOTER: '/voter',
    ELECTION_ADMIN: '/admin',
    AUDITOR: '/auditor',
  }

  const dashboardPath = user ? dashboardRoutes[user.role] : null

  return (
    <div className="app">
      <nav className="navbar">
        <Link to="/" className="logo">Campus Election 2.0</Link>
        <div className="nav-links">
          <a href="#features">Features</a>
          <a href="#about">About</a>
          {user ? (
            <>
              {dashboardPath && (
                <Link to={dashboardPath} className="nav-login">
                  Dashboard
                </Link>
              )}
              <button type="button" className="nav-login" onClick={logout}>
                Logout
              </button>
            </>
          ) : (
            <Link to="/login" className="nav-login">Login</Link>
          )}
        </div>
      </nav>

      <main>
        <section className="hero">
          <div className="hero-content">
            <span className="hero-badge">
              Secure Digital Campus Elections
            </span>
            <h1>Your Vote.<br /><span>Your Voice.</span></h1>
            <p>
              Campus Election 2.0 brings secure, transparent, and accessible
              elections to your campus. Every vote matters.
            </p>
            <div className="hero-buttons">
              {user && dashboardPath ? (
                <Link to={dashboardPath} className="btn-primary">
                  Go to Dashboard
                </Link>
              ) : (
                <Link to="/login" className="btn-primary">Get Started</Link>
              )}
              <a href="#features" className="btn-secondary">
                Explore Features
              </a>
            </div>
          </div>
        </section>

        <section className="features" id="features">
          <div className="section-title">
            <span>WHY CAMPUS ELECTION 2.0?</span>
            <h2>Built for Trust and Transparency</h2>
            <p>
              Modern election technology designed to make campus democracy
              safer, simpler, and more reliable.
            </p>
          </div>
          <div className="feature-grid">
            <article className="feature-card">
              <div className="feature-icon">🔒</div>
              <h3>Secure Voting</h3>
              <p>
                Authentication and server-side authorization help protect
                the integrity of the voting process.
              </p>
            </article>
            <article className="feature-card">
              <div className="feature-icon">✓</div>
              <h3>Transparent Process</h3>
              <p>
                Election statuses and published results help voters follow
                the election process.
              </p>
            </article>
            <article className="feature-card">
              <div className="feature-icon">⚡</div>
              <h3>Simple and Accessible</h3>
              <p>
                A clear digital interface makes it easier to access
                election information and participate.
              </p>
            </article>
          </div>
        </section>

        <section className="about-section" id="about">
          <div className="section-title">
            <span>ABOUT THE PROJECT</span>
            <h2>Modernizing Campus Elections</h2>
            <p>
              Campus Election 2.0 supports an organized digital election
              experience, with dedicated access for voters, election
              administrators, and auditors.
            </p>
          </div>
          {!user && (
            <div className="about-action">
              <Link to="/login" className="btn-primary">
                Login to Continue
              </Link>
            </div>
          )}
        </section>
      </main>

      <footer className="home-footer">
        <p>Campus Election 2.0 · Secure · Transparent · Fair</p>
      </footer>
    </div>
  )
}

function DashboardPlaceholder({ title, description }) {
  const { user, logout } = useAuth()

  return (
    <div className="dashboard-placeholder">
      <header className="dashboard-header">
        <Link to="/" className="dashboard-brand">
          <span className="brand-mark">CE</span>
          <span>
            Campus Election
            <small>Secure • Transparent • Fair</small>
          </span>
        </Link>
        <div className="dashboard-user">
          <span className="user-avatar">
            {(user?.username || 'U').charAt(0).toUpperCase()}
          </span>
          <div className="user-details">
            <strong>{user?.username || 'User'}</strong>
            <small>{user?.role || 'User'}</small>
          </div>
          <button type="button" className="dashboard-logout" onClick={logout}>
            Logout
          </button>
        </div>
      </header>
      <main className="dashboard-main">
        <section className="dashboard-welcome">
          <div>
            <span className="dashboard-eyebrow">CAMPUS ELECTION 2.0</span>
            <h1>{title}</h1>
            <p>{description}</p>
          </div>
        </section>
        <div className="dashboard-empty">
          <h3>Dashboard under development</h3>
          <p>
            This section will be connected to the election backend in a
            subsequent development step.
          </p>
          <Link to="/" className="election-open-button">Return to Home</Link>
        </div>
      </main>
    </div>
  )
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />

      <Route path="/voter" element={
        <ProtectedRoute allowedRoles={['VOTER']}>
          <VoterDashboard />
        </ProtectedRoute>
      } />

      <Route path="/voter/elections/:electionId" element={
        <ProtectedRoute allowedRoles={['VOTER']}>
          <ElectionDetails />
        </ProtectedRoute>
      } />

      <Route path="/admin" element={
        <ProtectedRoute allowedRoles={['ELECTION_ADMIN']}>
          <DashboardPlaceholder
            title="Election Administration"
            description="Manage elections, candidates, schedules, and voter eligibility."
          />
        </ProtectedRoute>
      } />

      <Route path="/auditor" element={
        <ProtectedRoute allowedRoles={['AUDITOR']}>
          <AuditDashboard />
        </ProtectedRoute>
      } />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}

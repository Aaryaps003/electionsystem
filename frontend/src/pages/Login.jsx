import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  Eye,
  EyeOff,
  LockKeyhole,
  ShieldCheck,
  Vote,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const roleDestinations = {
  VOTER: '/voter',
  ELECTION_ADMIN: '/admin',
  AUDITOR: '/auditor',
}

export default function Login() {
  const { login, user } = useAuth()
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (user) {
    return <Navigate to={roleDestinations[user.role] || '/'} replace />
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      const profile = await login(username.trim(), password)
      navigate(roleDestinations[profile.role] || '/', { replace: true })
    } catch (err) {
      const status = err.response?.status

      if (status === 401) {
        setError('Incorrect username or password. Please try again.')
      } else if (status === 403) {
        setError('Your account does not have permission to sign in.')
      } else {
        setError(
          'Unable to connect to the election server. Check that Django is running and try again.',
        )
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="login-page">
      <div className="login-decoration login-decoration-one" />
      <div className="login-decoration login-decoration-two" />

      <Link to="/" className="login-back">
        <ArrowLeft size={17} /> Back to home
      </Link>

      <section className="login-card">
        <div className="login-brand-icon">
          <Vote size={30} />
        </div>

        <span className="login-kicker">CAMPUS ELECTION 2.0</span>
        <h1>Welcome back.</h1>
        <p className="login-subtitle">
          Sign in to securely access your election workspace.
        </p>

        <div className="login-security-note">
          <ShieldCheck size={19} />
          <span>Your session is authenticated through the election server.</span>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            name="username"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Enter your username"
            required
            autoFocus
          />

          <div className="password-label-row">
            <label htmlFor="password">Password</label>
          </div>

          <div className="password-input-wrap">
            <LockKeyhole size={17} className="password-lock-icon" />
            <input
              id="password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              required
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          {error && (
            <div className="login-error" role="alert">
              {error}
            </div>
          )}

          <button
            className="login-submit"
            type="submit"
            disabled={submitting}
          >
            {submitting ? 'Signing in…' : 'Sign in securely'}
            {!submitting && <ArrowRight size={18} />}
          </button>
        </form>

        <div className="login-divider">
          <span />
          <span>AUTHORIZED ACCESS</span>
          <span />
        </div>

        <p className="login-footnote">
          Access is subject to your assigned account role and permissions.
        </p>
      </section>

      <p className="login-footer">
        Campus Election 2.0 <span>·</span> Digital democracy
      </p>
    </main>
  )
}

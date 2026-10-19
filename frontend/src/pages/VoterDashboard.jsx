
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { CalendarDays, Clock, RefreshCw, Vote } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { getElections, getEligibility } from '../api/elections'
import '../App.css'

function formatDate(value) {
  if (!value) return 'Not specified'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return 'Not specified'

  return date.toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function statusClass(status) {
  return `election-status status-${String(status || 'unknown')
    .toLowerCase()
    .replaceAll('_', '-')}`
}

export default function VoterDashboard() {
  const { user, accessToken, logout } = useAuth()

  const [elections, setElections] = useState([])
  const [eligibility, setEligibility] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadDashboard = useCallback(async () => {
    if (!accessToken) {
      setError('Your session has expired. Please log in again.')
      setLoading(false)
      return
    }

    setLoading(true)
    setError('')

    try {
      const data = await getElections(accessToken)
      const electionList = Array.isArray(data) ? data : data.results || []

      setElections(electionList)

      const eligibilityResults = await Promise.all(
        electionList.map(async (election) => {
          try {
            const result = await getEligibility(election.id, accessToken)
            return [election.id, result]
          } catch {
            return [
              election.id,
              {
                eligible: false,
                has_voted: false,
                can_vote: false,
                message: 'Eligibility information is currently unavailable.',
              },
            ]
          }
        }),
      )

      setEligibility(Object.fromEntries(eligibilityResults))
    } catch (err) {
      if (err.response?.status === 401) {
        setError('Your session has expired. Please log in again.')
      } else {
        setError(
          err.response?.data?.detail ||
            'Could not load elections. Check that the Django server is running.',
        )
      }
    } finally {
      setLoading(false)
    }
  }, [accessToken])

  useEffect(() => {
    loadDashboard()
  }, [loadDashboard])

  return (
    <div className="voter-dashboard">
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
            {(user?.username || 'V').charAt(0).toUpperCase()}
          </span>
          <div className="user-details">
            <strong>{user?.username || 'Voter'}</strong>
            <small>Registered Voter</small>
          </div>
          <button
            className="dashboard-logout"
            onClick={logout}
            type="button"
          >
            Logout
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        <section className="dashboard-welcome">
          <div>
            <span className="dashboard-eyebrow">VOTER PORTAL</span>
            <h1>Welcome, {user?.username || 'Voter'}!</h1>
            <p>
              View available elections, check your eligibility, and make
              your voice count.
            </p>
          </div>

          <div className="welcome-icon">
            <Vote size={38} />
          </div>
        </section>

        <section className="elections-section">
          <div className="section-heading">
            <div>
              <h2>Available Elections</h2>
              <p>Election information provided by the server.</p>
            </div>

            <button
              className="refresh-button"
              type="button"
              onClick={loadDashboard}
              disabled={loading}
            >
              <RefreshCw size={16} />
              Refresh
            </button>
          </div>

          {loading && (
            <div className="dashboard-message">
              <div className="loading-spinner" />
              <p>Loading elections and checking eligibility...</p>
            </div>
          )}

          {!loading && error && (
            <div className="dashboard-error">
              <p>{error}</p>
              <button type="button" onClick={loadDashboard}>
                Try again
              </button>
            </div>
          )}

          {!loading && !error && elections.length === 0 && (
            <div className="dashboard-empty">
              <Vote size={34} />
              <h3>No elections available</h3>
              <p>
                There are currently no published elections to display.
              </p>
            </div>
          )}

          {!loading && !error && elections.length > 0 && (
            <div className="election-grid">
              {elections.map((election) => {
                const result = eligibility[election.id]

                return (
                  <article className="election-card" key={election.id}>
                    <div className="election-card-top">
                      <span className="election-number">
                        ELECTION #{election.id}
                      </span>
                      <span className={statusClass(election.status)}>
                        {String(election.status || 'UNKNOWN').replaceAll(
                          '_',
                          ' ',
                        )}
                      </span>
                    </div>

                    <h3>{election.title}</h3>

                    <p className="election-description">
                      {election.description || 'No description provided.'}
                    </p>

                    <div className="election-date">
                      <CalendarDays size={17} />
                      <div>
                        <small>Starts</small>
                        <span>{formatDate(election.start_time)}</span>
                      </div>
                    </div>

                    <div className="election-date">
                      <Clock size={17} />
                      <div>
                        <small>Ends</small>
                        <span>{formatDate(election.end_time)}</span>
                      </div>
                    </div>

                    <div className="eligibility-panel">
                      <strong>
                        {result
                          ? result.has_voted
                            ? 'Vote already recorded'
                            : result.can_vote
                              ? 'You can vote in this election'
                              : result.eligible
                                ? 'Eligible voter'
                                : 'Eligibility not confirmed'
                          : 'Checking eligibility...'}
                      </strong>

                      <p>
                        {result?.message ||
                          'Checking your voting permissions.'}
                      </p>
                    </div>

                    <Link
                      to={`/voter/elections/${election.id}`}
                      className="election-open-button"
                    >
                      View Election
                    </Link>
                  </article>
                )
              })}
            </div>
          )}
        </section>

        <footer className="dashboard-footer">
          Campus Election 2.0 · Secure digital campus elections
        </footer>
      </main>
    </div>
  )
}

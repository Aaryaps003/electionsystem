import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Activity, ArrowLeft, CheckCircle2, CircleAlert, Clock,
  FileSearch, Fingerprint, RefreshCw, Search, ShieldCheck, ShieldX,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import api from '../api/client'

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString()
}

function formatEventType(value) {
  return String(value || 'Unknown event')
    .replaceAll('_', ' ')
    .toLowerCase()
    .replace(/\b\w/g, letter => letter.toUpperCase())
}

function extractEvents(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.results)) return data.results
  if (Array.isArray(data?.events)) return data.events
  return []
}

export default function AuditDashboard() {
  const { accessToken, user, logout } = useAuth()
  const [events, setEvents] = useState([])
  const [electionId, setElectionId] = useState('')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [verification, setVerification] = useState(null)
  const [verifying, setVerifying] = useState(false)
  const [verificationError, setVerificationError] = useState('')

  const authConfig = useMemo(() => ({
    headers: { Authorization: `Bearer ${accessToken}` },
  }), [accessToken])

  const loadEvents = useCallback(async (isRefresh = false) => {
    if (!accessToken) {
      setError('Your session is missing. Please log in again.')
      setLoading(false)
      return
    }

    if (isRefresh) setRefreshing(true)
    else setLoading(true)

    setError('')

    try {
      const params = electionId.trim()
        ? { election_id: electionId.trim() }
        : {}

      const response = await api.get('/audit/events/', {
        ...authConfig,
        params,
      })
      setEvents(extractEvents(response.data))
    } catch (err) {
      setError(
        err.response?.status === 403
          ? 'Access denied. This dashboard is restricted to auditors.'
          : err.response?.status === 401
            ? 'Your session has expired. Please log in again.'
            : err.response?.data?.detail ||
              'Could not load audit events. Check the Django server.'
      )
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [accessToken, authConfig, electionId])

  const verifyIntegrity = useCallback(async () => {
    if (!accessToken) {
      setVerificationError('Please log in again.')
      return
    }

    setVerifying(true)
    setVerificationError('')
    setVerification(null)

    try {
      const response = await api.get('/audit/verify/', authConfig)
      setVerification(response.data)
    } catch (err) {
      if (err.response?.status === 409 && err.response.data) {
        setVerification(err.response.data)
      } else {
        setVerificationError(
          err.response?.data?.detail ||
          'Integrity verification could not be completed.'
        )
      }
    } finally {
      setVerifying(false)
    }
  }, [accessToken, authConfig])

  useEffect(() => {
    loadEvents()
  }, [loadEvents])

  const filteredEvents = useMemo(() => {
    const term = search.trim().toLowerCase()
    if (!term) return events

    return events.filter(event => [
      event.id,
      event.event_type,
      event.election_title,
      event.actor_username,
      event.timestamp,
      JSON.stringify(event.metadata ?? {}),
    ].join(' ').toLowerCase().includes(term))
  }, [events, search])

  const chainValid = verification?.valid === true
  const chainInvalid = verification?.valid === false

  return (
    <div className="audit-dashboard">
      <header className="audit-header">
        <Link to="/" className="audit-brand">
          <span className="audit-brand-mark">CE</span>
          <span>
            Campus Election 2.0
            <small>Secure · Transparent · Fair</small>
          </span>
        </Link>

        <div className="audit-user">
          <span className="audit-avatar">
            {(user?.username || 'A').charAt(0).toUpperCase()}
          </span>
          <div className="audit-user-details">
            <strong>{user?.username || 'Auditor'}</strong>
            <small>Auditor</small>
          </div>
          <button className="audit-logout" onClick={logout} type="button">
            Logout
          </button>
        </div>
      </header>

      <main className="audit-main">
        <Link to="/" className="audit-back">
          <ArrowLeft size={16} /> Return to Home
        </Link>

        <section className="audit-hero">
          <div className="audit-hero-icon"><ShieldCheck size={32} /></div>
          <span className="audit-eyebrow">CAMPUS ELECTION 2.0</span>
          <h1>Audit Dashboard</h1>
          <p>
            Review election activity and verify the integrity of the
            tamper-evident audit log.
          </p>
        </section>

        <section className="audit-summary-grid">
          <article className="audit-summary-card">
            <Activity size={22} />
            <span>Loaded events</span>
            <strong>{events.length}</strong>
            <small>Records returned by the API</small>
          </article>
          <article className="audit-summary-card">
            <FileSearch size={22} />
            <span>Matching events</span>
            <strong>{filteredEvents.length}</strong>
            <small>After search filtering</small>
          </article>
          <article className="audit-summary-card">
            <Fingerprint size={22} />
            <span>Chain integrity</span>
            <strong className={
              chainValid ? 'audit-valid-text' :
              chainInvalid ? 'audit-invalid-text' : ''
            }>
              {chainValid ? 'Valid' : chainInvalid ? 'Invalid' : 'Not checked'}
            </strong>
            <small>Reported by the backend</small>
          </article>
        </section>

        <section className="audit-integrity-panel">
          <div>
            <span className="audit-section-eyebrow">SECURITY CHECK</span>
            <h2>Audit Chain Verification</h2>
            <p>
              Ask Django to verify the stored audit chain. The result comes
              from the server, not from the browser.
            </p>

            {verification && (
              <div className={`audit-verification-result ${
                chainValid ? 'is-valid' : 'is-invalid'
              }`} role="status">
                {chainValid
                  ? <CheckCircle2 size={20} />
                  : <ShieldX size={20} />}
                <div>
                  <strong>
                    {chainValid ? 'Integrity check passed' :
                     chainInvalid ? 'Integrity check failed' :
                     'Verification response received'}
                  </strong>
                  <p>
                    {verification.message || verification.detail ||
                     (chainValid
                       ? 'The backend reports a valid audit chain.'
                       : 'The backend reports an invalid audit chain.')}
                  </p>
                </div>
              </div>
            )}

            {verificationError && (
              <p className="audit-error-text" role="alert">
                {verificationError}
              </p>
            )}
          </div>

          <button className="audit-primary-button" type="button"
            onClick={verifyIntegrity} disabled={verifying}>
            <ShieldCheck size={17} />
            {verifying ? 'Verifying…' : 'Verify Integrity'}
          </button>
        </section>

        <section className="audit-events-section">
          <div className="audit-section-heading">
            <div>
              <span className="audit-section-eyebrow">RECORDS</span>
              <h2>Audit Events</h2>
              <p>Inspect recorded activity and associated hash values.</p>
            </div>
            <button className="audit-secondary-button" type="button"
              onClick={() => loadEvents(true)}
              disabled={refreshing || loading}>
              <RefreshCw size={16} className={
                refreshing ? 'audit-spinning' : ''
              } />
              {refreshing ? 'Refreshing…' : 'Refresh'}
            </button>
          </div>

          <div className="audit-filters">
            <label className="audit-search">
              <Search size={17} />
              <input type="search"
                placeholder="Search events, actors, metadata…"
                value={search}
                onChange={event => setSearch(event.target.value)} />
            </label>

            <label className="audit-election-filter">
              <span>Election ID</span>
              <input type="number" min="1" step="1"
                placeholder="All"
                value={electionId}
                onChange={event => setElectionId(event.target.value)} />
            </label>

            <button className="audit-secondary-button" type="button"
              onClick={() => {
                setElectionId('')
                setSearch('')
              }}>
              Clear filters
            </button>
          </div>

          {error && (
            <div className="audit-alert" role="alert">
              <CircleAlert size={21} />
              <div>
                <strong>Unable to load audit events</strong>
                <p>{error}</p>
                <button className="audit-inline-button" type="button"
                  onClick={() => loadEvents(true)}>
                  Try again
                </button>
              </div>
            </div>
          )}

          {loading && (
            <div className="audit-state">
              <span className="audit-loader" />
              <p>Loading audit events…</p>
            </div>
          )}

          {!loading && !error && filteredEvents.length === 0 && (
            <div className="audit-state">
              <FileSearch size={32} />
              <h3>No audit events found</h3>
              <p>
                {events.length
                  ? 'Try changing your search or election filter.'
                  : 'The API returned no audit events for this filter.'}
              </p>
            </div>
          )}

          {!loading && !error && filteredEvents.length > 0 && (
            <div className="audit-table-wrap">
              <table className="audit-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Event</th>
                    <th>Election</th>
                    <th>Actor</th>
                    <th>Timestamp</th>
                    <th>Event hash</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEvents.map(event => (
                    <tr key={event.id}>
                      <td>#{event.id}</td>
                      <td>
                        <span className="audit-event-type">
                          {formatEventType(event.event_type)}
                        </span>
                        <details className="audit-metadata">
                          <summary>View metadata and hashes</summary>
                          <pre>{JSON.stringify(
                            event.metadata ?? {}, null, 2
                          )}</pre>
                          <div>
                            <strong>Previous hash</strong>
                            <code>{event.previous_hash || 'None'}</code>
                          </div>
                          <div>
                            <strong>Event hash</strong>
                            <code>{event.event_hash || 'Unavailable'}</code>
                          </div>
                        </details>
                      </td>
                      <td>
                        {event.election_title ||
                          (event.election
                            ? `Election ${event.election}`
                            : 'System event')}
                      </td>
                      <td>{event.actor_username || 'System / anonymous'}</td>
                      <td>
                        <span className="audit-timestamp">
                          <Clock size={14} />
                          {formatDate(event.timestamp)}
                        </span>
                      </td>
                      <td>
                        <code title={event.event_hash || ''}>
                          {event.event_hash
                            ? `${event.event_hash.slice(0, 12)}…`
                            : 'Unavailable'}
                        </code>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <p className="audit-disclaimer">
            Audit records are read-only. Access control and integrity
            verification are enforced by Django.
          </p>
        </section>

        <footer className="audit-footer">
          Campus Election 2.0 · Audit and Integrity
        </footer>
      </main>
    </div>
  )
}

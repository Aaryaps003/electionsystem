
import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  ShieldCheck,
  Vote,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import {
  getElection,
  getCandidates,
  getEligibility,
  castVote,
} from '../api/elections'

function formatDate(value) {
  if (!value) return 'Not specified'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return 'Not specified'

  return date.toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function getErrorMessage(error) {
  const data = error.response?.data

  if (typeof data?.detail === 'string') return data.detail

  if (data && typeof data === 'object') {
    return Object.values(data)
      .flat()
      .filter((value) => typeof value === 'string')
      .join(' ')
  }

  return 'Something went wrong. Please try again.'
}

export default function ElectionDetails() {
  const { electionId } = useParams()
  const { user, accessToken } = useAuth()

  const [election, setElection] = useState(null)
  const [candidates, setCandidates] = useState([])
  const [eligibility, setEligibility] = useState(null)
  const [selectedCandidate, setSelectedCandidate] = useState(null)

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [voteMessage, setVoteMessage] = useState('')
  const [voteError, setVoteError] = useState('')

  const loadElection = useCallback(async () => {
    if (!accessToken) {
      setError('Your session has expired. Please sign in again.')
      setLoading(false)
      return
    }

    setLoading(true)
    setError('')

    try {
      const [electionData, candidateData, eligibilityData] =
        await Promise.all([
          getElection(electionId, accessToken),
          getCandidates(electionId, accessToken),
          getEligibility(electionId, accessToken),
        ])

      setElection(electionData)

      const candidateList = Array.isArray(candidateData)
        ? candidateData
        : candidateData.results || []

      setCandidates(candidateList)
      setEligibility(eligibilityData)
    } catch (err) {
      setError(
        err.response?.status === 401
          ? 'Your session has expired. Please sign in again.'
          : getErrorMessage(err),
      )
    } finally {
      setLoading(false)
    }
  }, [electionId, accessToken])

  useEffect(() => {
    loadElection()
  }, [loadElection])

  async function handleVote() {
    if (!selectedCandidate || !eligibility?.can_vote || submitting) {
      return
    }

    const candidate = candidates.find(
      (item) => item.id === selectedCandidate,
    )

    if (!candidate) {
      setVoteError('Please select a valid candidate.')
      return
    }

    const confirmed = window.confirm(
      `Are you sure you want to vote for ${candidate.name}?\n\n` +
        'Please verify your choice. You cannot change your vote after it is recorded.',
    )

    if (!confirmed) return

    setSubmitting(true)
    setVoteError('')
    setVoteMessage('')

    try {
      const result = await castVote(
        electionId,
        selectedCandidate,
        accessToken,
      )

      setVoteMessage(
        result.detail || 'Your vote was recorded successfully.',
      )
      setSelectedCandidate(null)

      // Re-fetch server-side eligibility after a successful vote.
      const updatedEligibility = await getEligibility(
        electionId,
        accessToken,
      )

      setEligibility(updatedEligibility)
    } catch (err) {
      setVoteError(
        getErrorMessage(err),
      )

      // Refresh eligibility in case the server recorded the vote
      // but the response was interrupted.
      try {
        const updatedEligibility = await getEligibility(
          electionId,
          accessToken,
        )
        setEligibility(updatedEligibility)
      } catch {
        // Preserve the original voting error.
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <main className="election-details-page">
        <div className="election-details-container">
          <div className="dashboard-message">
            <div className="loading-spinner" />
            <p>Loading election details...</p>
          </div>
        </div>
      </main>
    )
  }

  if (error && !election) {
    return (
      <main className="election-details-page">
        <div className="election-details-container">
          <Link to="/voter" className="details-back-link">
            <ArrowLeft size={17} />
            Back to dashboard
          </Link>

          <div className="dashboard-error">
            <h2>Unable to load election</h2>
            <p>{error}</p>
            <button type="button" onClick={loadElection}>
              Try again
            </button>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="election-details-page">
      <div className="election-details-container">
        <header className="details-header">
          <Link to="/voter" className="details-back-link">
            <ArrowLeft size={17} />
            Back to dashboard
          </Link>

          <div className="details-user">
            <span className="user-avatar">
              {(user?.username || 'V').charAt(0).toUpperCase()}
            </span>
            <span>{user?.username || 'Voter'}</span>
          </div>
        </header>

        <section className="details-hero">
          <span className="dashboard-eyebrow">
            ELECTION #{election.id}
          </span>

          <h1>{election.title}</h1>

          <p>
            {election.description || 'No election description provided.'}
          </p>

          <span
            className={`election-status status-${String(
              election.status || 'unknown',
            )
              .toLowerCase()
              .replaceAll('_', '-')}`}
          >
            {String(election.status || 'UNKNOWN').replaceAll('_', ' ')}
          </span>
        </section>

        <section className="details-info-grid">
          <article className="details-info-card">
            <Clock size={20} />
            <div>
              <span>Election starts</span>
              <strong>{formatDate(election.start_time)}</strong>
            </div>
          </article>

          <article className="details-info-card">
            <Clock size={20} />
            <div>
              <span>Election ends</span>
              <strong>{formatDate(election.end_time)}</strong>
            </div>
          </article>
        </section>

        {eligibility && (
          <section
            className={`voting-eligibility ${
              eligibility.can_vote
                ? 'eligibility-allowed'
                : 'eligibility-restricted'
            }`}
          >
            <ShieldCheck size={23} />

            <div>
              <strong>
                {eligibility.can_vote
                  ? 'You are eligible to vote'
                  : eligibility.has_voted
                    ? 'Your vote has already been recorded'
                    : 'Voting is currently unavailable'}
              </strong>

              <p>{eligibility.message}</p>
            </div>
          </section>
        )}

        {voteMessage && (
          <div className="vote-feedback vote-feedback-success" role="status">
            <CheckCircle2 size={20} />
            <p>{voteMessage}</p>
          </div>
        )}

        {voteError && (
          <div className="vote-feedback vote-feedback-error" role="alert">
            <p>{voteError}</p>
          </div>
        )}

        <section className="candidate-section">
          <div className="candidate-section-heading">
            <div>
              <span className="dashboard-eyebrow">YOUR CHOICE MATTERS</span>
              <h2>Meet the Candidates</h2>
              <p>Review each candidate before making your selection.</p>
            </div>

            <Vote size={30} />
          </div>

          {candidates.length === 0 ? (
            <div className="dashboard-empty">
              <h3>No candidates available</h3>
              <p>
                No candidates have been added to this election yet.
              </p>
            </div>
          ) : (
            <div className="candidate-grid">
              {candidates.map((candidate) => {
                const selected = selectedCandidate === candidate.id

                return (
                  <article
                    className={`candidate-card ${
                      selected ? 'candidate-selected' : ''
                    }`}
                    key={candidate.id}
                  >
                    {candidate.photo_url ? (
                      <img
                        className="candidate-photo"
                        src={candidate.photo_url}
                        alt={candidate.name}
                        onError={(event) => {
                          event.currentTarget.style.display = 'none'
                        }}
                      />
                    ) : (
                      <div className="candidate-photo-placeholder">
                        {(candidate.name || 'C')
                          .charAt(0)
                          .toUpperCase()}
                      </div>
                    )}

                    <div className="candidate-card-content">
                      <h3>{candidate.name}</h3>

                      <span className="candidate-id">
                        Candidate #{candidate.id}
                      </span>

                      <h4>Manifesto</h4>

                      <p>
                        {candidate.manifesto ||
                          'No manifesto has been provided.'}
                      </p>

                      {eligibility?.can_vote && (
                        <button
                          type="button"
                          className={`candidate-select-button ${
                            selected ? 'candidate-select-active' : ''
                          }`}
                          onClick={() => {
                            setSelectedCandidate(candidate.id)
                            setVoteError('')
                          }}
                        >
                          {selected ? (
                            <>
                              <CheckCircle2 size={17} />
                              Selected
                            </>
                          ) : (
                            'Select candidate'
                          )}
                        </button>
                      )}
                    </div>
                  </article>
                )
              })}
            </div>
          )}

          {eligibility?.can_vote && candidates.length > 0 && (
            <div className="vote-submit-panel">
              <div>
                <strong>Ready to cast your vote?</strong>
                <p>
                  {selectedCandidate
                    ? 'Review your selection before continuing.'
                    : 'Select one candidate to continue.'}
                </p>
              </div>

              <button
                type="button"
                className="cast-vote-button"
                disabled={!selectedCandidate || submitting}
                onClick={handleVote}
              >
                {submitting ? 'Submitting...' : 'Confirm and Vote'}
              </button>
            </div>
          )}
        </section>

        <footer className="dashboard-footer">
          Campus Election 2.0 · Your vote matters
        </footer>
      </div>
    </main>
  )
}


import api from './client'

const authConfig = (token) => ({
  headers: {
    Authorization: `Bearer ${token}`,
  },
})

export async function getElections(token) {
  const response = await api.get('/elections/', authConfig(token))
  return response.data
}

export async function getElection(electionId, token) {
  const response = await api.get(
    `/elections/${electionId}/`,
    authConfig(token),
  )
  return response.data
}

export async function getCandidates(electionId, token) {
  const response = await api.get(
    `/elections/${electionId}/candidates/`,
    authConfig(token),
  )
  return response.data
}

export async function getEligibility(electionId, token) {
  const response = await api.get(
    `/voting/eligibility/${electionId}/`,
    authConfig(token),
  )
  return response.data
}

export async function castVote(electionId, candidateId, token) {
  const response = await api.post(
    '/voting/cast/',
    {
      election_id: electionId,
      candidate_id: candidateId,
    },
    authConfig(token),
  )
  return response.data
}

import { apiRequest } from './api'

export function createPatient(data) {
  return apiRequest('/api/patients', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function listPatients() {
  return apiRequest('/api/patients')
}

export function getPatient(id) {
  return apiRequest(`/api/patients/${id}`)
}

export function updatePatient(id, data) {
  return apiRequest(`/api/patients/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export function comparePatientSessions(patientId, sessionA, sessionB) {
  return apiRequest(`/api/patients/${patientId}/sessions/compare?session_a=${sessionA}&session_b=${sessionB}`)
}

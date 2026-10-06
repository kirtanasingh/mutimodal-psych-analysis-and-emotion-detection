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

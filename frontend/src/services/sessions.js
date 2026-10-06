import { apiRequest, getAuthHeaders } from './api'

export function createSession(data) {
  return apiRequest('/api/sessions', { method: 'POST', body: JSON.stringify(data) })
}

export function getSession(id) {
  return apiRequest(`/api/sessions/${id}`)
}

export function uploadSessionVideo(id, file, onProgress) {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest()
    request.open('POST', `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/sessions/${id}/upload`)
    Object.entries(getAuthHeaders()).forEach(([key, value]) => request.setRequestHeader(key, value))
    request.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) onProgress(Math.round((event.loaded / event.total) * 100))
    })
    request.addEventListener('load', () => {
      let body = {}
      try { body = JSON.parse(request.responseText) } catch { /* status carries the error */ }
      if (request.status >= 200 && request.status < 300) resolve(body)
      else reject(new Error(body.detail || 'Video upload failed'))
    })
    request.addEventListener('error', () => reject(new Error('Video upload failed')))
    const formData = new FormData()
    formData.append('video', file)
    request.send(formData)
  })
}

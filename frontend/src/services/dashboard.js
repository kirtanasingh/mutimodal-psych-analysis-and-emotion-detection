import { apiRequest } from './api'

export const getDashboardSummary = () => apiRequest('/api/dashboard/summary')
export const getRecentSessions = () => apiRequest('/api/dashboard/recent-sessions')
export const getRecentReports = () => apiRequest('/api/dashboard/recent-reports')
export const getPriorityQueue = () => apiRequest('/api/dashboard/priority-queue')
export const getCaseloadSnapshot = (days = 7) => apiRequest(`/api/dashboard/caseload-snapshot?days=${days}`)

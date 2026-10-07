import { createContext, useContext, useState } from 'react'
import { apiRequest } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('access_token'))
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('auth_user') || 'null') } catch { return null }
  })

  function persist(result) {
    localStorage.setItem('access_token', result.access_token)
    localStorage.setItem('auth_user', JSON.stringify(result.user))
    setToken(result.access_token)
    setUser(result.user)
  }

  async function login(email, password) {
    const result = await apiRequest('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) })
    persist(result)
  }

  async function signup(displayName, email, password) {
    const result = await apiRequest('/api/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ display_name: displayName, email, password }),
    })
    persist(result)
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('auth_user')
    setToken(null)
    setUser(null)
  }

  const value = { user, token, login, signup, logout }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// The hook intentionally lives beside its provider so auth state has one public API.
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext)
}

import { useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import PatientProfile from './pages/PatientProfile'
import Patients from './pages/Patients'
import NewSession from './pages/NewSession'
import SessionProfile from './pages/SessionProfile'
import { apiRequest } from './services/api'
import './App.css'

function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('psychologist@example.com')
  const [password, setPassword] = useState('devpassword123')
  const [error, setError] = useState('')
  async function submit(event) {
    event.preventDefault()
    try {
      const result = await apiRequest('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) })
      localStorage.setItem('access_token', result.access_token)
      navigate('/patients')
    } catch (err) { setError(err.message) }
  }
  return <main className="login"><form className="modal login-card" onSubmit={submit}><span className="eyebrow">Clinical Workspace</span><h1>Sign in</h1><label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label><label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>{error && <p className="error">{error}</p>}<button className="button primary">Sign in</button></form></main>
}

function ProtectedLayout() {
  return <><Sidebar /><Routes><Route path="/" element={<main className="page"><h1>Dashboard</h1><p className="muted">Dashboard placeholder.</p></main>} /><Route path="/patients" element={<Patients />} /><Route path="/patients/:id" element={<PatientProfile />} /><Route path="/sessions/new" element={<NewSession />} /><Route path="/sessions/:id" element={<SessionProfile />} /><Route path="*" element={<Navigate to="/patients" replace />} /></Routes></>
}

export default function App() {
  const [authenticated] = useState(() => Boolean(localStorage.getItem('access_token')))
  return <BrowserRouter>{authenticated ? <ProtectedLayout /> : <Routes><Route path="*" element={<Login />} /></Routes>}</BrowserRouter>
}

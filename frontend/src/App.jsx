import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import PatientProfile from './pages/PatientProfile'
import Patients from './pages/Patients'
import NewSession from './pages/NewSession'
import SessionProfile from './pages/SessionProfile'
import Dashboard from './pages/Dashboard'
import SessionCompare from './pages/SessionCompare'
import Reports from './pages/Reports'
import { Login, Signup } from './pages/AuthPages'
import { AuthProvider, useAuth } from './context/AuthContext'
import './App.css'

function ProtectedLayout() {
  const { token } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  return <div className="app-shell"><Sidebar /><div className="content-shell"><Routes>
    <Route path="/" element={<Dashboard />} />
    <Route path="/patients" element={<Patients />} />
    <Route path="/patients/:id" element={<PatientProfile />} />
    <Route path="/patients/:patientId/compare" element={<SessionCompare />} />
    <Route path="/sessions/new" element={<NewSession />} />
    <Route path="/sessions/:id" element={<SessionProfile />} />
    <Route path="/reports" element={<Reports />} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></div></div>
}

function AppRoutes() {
  const { token } = useAuth()
  return <Routes>
    <Route path="/login" element={token ? <Navigate to="/" replace /> : <Login />} />
    <Route path="/signup" element={token ? <Navigate to="/" replace /> : <Signup />} />
    <Route path="*" element={<ProtectedLayout />} />
  </Routes>
}

export default function App() {
  return <BrowserRouter><AuthProvider><AppRoutes /></AuthProvider></BrowserRouter>
}

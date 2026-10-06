import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getSession } from '../services/sessions'

export default function SessionProfile() {
  const { id } = useParams()
  const [session, setSession] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getSession(id).then(setSession).catch((err) => setError(err.message))
  }, [id])

  if (error) return <main className="page"><p className="error">{error}</p></main>
  if (!session) return <main className="page"><p className="muted">Loading session...</p></main>
  return <main className="page">
    <Link className="back-link" to="/patients">← Patients</Link>
    <section className="info-card session-placeholder"><span className="eyebrow">Session</span><h1>Session #{session.id}</h1><p className="status-line">Status: <strong>{session.status}</strong></p><p className="muted">The analysis dashboard will be available in a future phase.</p></section>
  </main>
}

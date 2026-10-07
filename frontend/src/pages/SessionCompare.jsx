import { useEffect, useState } from 'react'
import { Link, useSearchParams, useParams } from 'react-router-dom'
import EmotionDistribution from '../components/EmotionDistribution'
import EmotionTimeline from '../components/EmotionTimeline'
import { comparePatientSessions } from '../services/patients'

export default function SessionCompare() {
  const { patientId } = useParams()
  const [params] = useSearchParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    comparePatientSessions(patientId, params.get('a'), params.get('b')).then(setData).catch((err) => setError(err.message))
  }, [patientId, params])
  if (error) return <main className="page"><p className="error">{error}</p></main>
  if (!data) return <main className="page"><p className="muted">Loading comparison...</p></main>
  return <main className="page"><Link className="back-link" to={`/patients/${patientId}`}>← Patient profile</Link><header className="page-header"><div><span className="eyebrow">Session comparison</span><h1>Detected model signals across sessions</h1></div></header><div className="comparison-grid">{[data.session_a, data.session_b].map((session) => <section className="comparison-column" key={session.id}><div className="info-card"><span className="eyebrow">Session #{session.id}</span><h2>{session.session_date}</h2><p className="muted">{session.duration_seconds ? `${Math.round(session.duration_seconds / 60)} minute session` : 'Duration unavailable'}</p></div><EmotionDistribution distribution={session.distribution} timeline={session.timeline} /><EmotionTimeline timeline={session.timeline} /></section>)}</div></main>
}

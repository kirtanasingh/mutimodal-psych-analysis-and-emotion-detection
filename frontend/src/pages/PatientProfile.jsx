import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getPatient, updatePatient } from '../services/patients'
import { EMOTION_COLORS } from '../constants/emotionColors'
import SessionFingerprint from '../components/SessionFingerprint'

export default function PatientProfile() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [patient, setPatient] = useState(null)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({ full_name: '', age: '', profession: '' })
  const [selectedSessions, setSelectedSessions] = useState([])
  async function refresh() {
    const data = await getPatient(id)
    setPatient(data)
    setForm({ full_name: data.full_name || '', age: data.age ?? '', profession: data.profession || '' })
  }
  useEffect(() => {
    let cancelled = false
    getPatient(id).then((data) => {
      if (cancelled) return
      setPatient(data)
      setForm({ full_name: data.full_name || '', age: data.age ?? '', profession: data.profession || '' })
    }).catch((err) => {
      if (!cancelled) setError(err.message)
    })
    return () => { cancelled = true }
  }, [id])
  if (error) return <main className="page"><p className="error">{error}</p></main>
  if (!patient) return <main className="page"><p className="muted">Loading patient...</p></main>
  const initial = patient.display_id.slice(-1)
  async function submitEdit(event) {
    event.preventDefault()
    try {
      await updatePatient(id, {
        full_name: form.full_name || null,
        age: form.age === '' ? null : Number(form.age),
        profession: form.profession || null,
      })
      await refresh()
      setEditing(false)
      setError('')
    } catch (err) { setError(err.message) }
  }
  function toggleSession(sessionId) {
    setSelectedSessions((current) => current.includes(sessionId)
      ? current.filter((value) => value !== sessionId)
      : current.length < 2 ? [...current, sessionId] : current)
  }
  return <main className="page">
    <Link className="back-link" to="/patients">← Patients</Link>
    <header className="profile-header"><div className="patient-card-heading"><span className="patient-avatar large">{initial}</span><div><span className="eyebrow">Patient profile</span><h1>{patient.display_id}</h1>{patient.full_name && <p className="muted">{patient.full_name}</p>}</div></div><div className="profile-actions"><button className="button" onClick={() => setEditing(true)}>Edit</button><button className="button primary" onClick={() => navigate(`/sessions/new?patient=${patient.id}`)}>New session for this patient</button></div></header>
    <section className="info-card"><h2>Basic information</h2><dl><div><dt>Full name</dt><dd>{patient.full_name || 'Not provided'}</dd></div><div><dt>Age</dt><dd>{patient.age ?? 'Not provided'}</dd></div><div><dt>Profession</dt><dd>{patient.profession || 'Not provided'}</dd></div>{Object.entries(patient.basic_info_json || {}).filter(([key, value]) => value && !['full_name', 'age', 'profession'].includes(key)).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{value}</dd></div>)}</dl></section>
    {patient.sessions.length > 1 && patient.sessions.some((session) => session.dominant_proportion != null) && <TrendChart sessions={patient.sessions} />}
    <section className="panel session-history"><div className="panel-heading"><div><span className="eyebrow">History</span><h2>Session history</h2></div>{selectedSessions.length === 2 && <button className="button primary small" onClick={() => navigate(`/patients/${patient.id}/compare?a=${selectedSessions[0]}&b=${selectedSessions[1]}`)}>Compare selected</button>}</div>{patient.sessions.length === 0 ? <div className="panel-empty"><p>No sessions yet.</p></div> : <div className="table-wrap"><table><thead><tr><th>Select</th><th>Date</th><th>Duration</th><th>Fingerprint</th><th>Status</th><th>Action</th></tr></thead><tbody>{patient.sessions.map((session) => <tr key={session.id}><td><input type="checkbox" checked={selectedSessions.includes(session.id)} onChange={() => toggleSession(session.id)} aria-label={`Select session ${session.id}`} /></td><td>{session.session_date}</td><td>{session.duration_seconds ? `${Math.round(session.duration_seconds / 60)} min` : '—'}</td><td><SessionFingerprint distribution={session.emotion_distribution} /></td><td><span className={`status-badge status-${session.status === 'analysis_complete' ? 'complete' : session.status === 'upload_failed' ? 'failed' : 'pending'}`}>{session.status.replaceAll('_', ' ')}</span></td><td><Link to={`/sessions/${session.id}`} className="table-link">Open session →</Link></td></tr>)}</tbody></table></div>}</section>
    {editing && <div className="modal-backdrop" role="dialog" aria-modal="true"><form className="modal" onSubmit={submitEdit}><h2>Edit patient</h2><p className="muted">Optional details stay under your control. The system-generated patient ID cannot be edited.</p><label>Patient ID<input value={patient.display_id} readOnly /></label><label>Full name<input value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} /></label><label>Age<input type="number" min="0" value={form.age} onChange={(event) => setForm({ ...form, age: event.target.value })} /></label><label>Profession<input value={form.profession} onChange={(event) => setForm({ ...form, profession: event.target.value })} /></label><div className="modal-actions"><button type="button" className="button" onClick={() => setEditing(false)}>Cancel</button><button className="button primary">Save changes</button></div></form></div>}
  </main>
}

function TrendChart({ sessions }) {
  const points = sessions.slice().reverse()
  return <section className="visual-card trend-card"><span className="eyebrow">Longitudinal context</span><h2>Detected model signal trend across sessions</h2><div className="trend-bars">{points.map((point) => <div className="trend-point" key={point.id}><div className="trend-bar"><span style={{ height: `${(point.dominant_proportion || 0) * 100}%`, background: EMOTION_COLORS[point.dominant_emotion] || '#8a94a6' }} /></div><small>{point.session_date.slice(5)}</small><b>{point.dominant_emotion || '—'}</b></div>)}</div></section>
}

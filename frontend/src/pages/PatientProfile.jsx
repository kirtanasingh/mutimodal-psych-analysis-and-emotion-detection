import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getPatient } from '../services/patients'

export default function PatientProfile() {
  const { id } = useParams()
  const [patient, setPatient] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getPatient(id).then(setPatient).catch((err) => setError(err.message))
  }, [id])

  if (error) return <main className="page"><p className="error">{error}</p></main>
  if (!patient) return <main className="page"><p className="muted">Loading patient...</p></main>

  return <main className="page">
    <Link className="back-link" to="/patients">← Patients</Link>
    <header className="profile-header"><div><span className="eyebrow">Patient profile</span><h1>{patient.display_id}</h1></div></header>
    <section className="info-card"><h2>Basic information</h2><dl>
      {Object.entries(patient.basic_info_json || {}).filter(([, value]) => value).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{value}</dd></div>)}
    </dl>{!Object.values(patient.basic_info_json || {}).some(Boolean) && <p className="muted">No basic information provided.</p>}</section>
    <section className="empty-state"><h2>No sessions yet</h2><p>Session history will appear here when sessions are added.</p></section>
  </main>
}

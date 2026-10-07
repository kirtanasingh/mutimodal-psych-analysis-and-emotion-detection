import { Link } from 'react-router-dom'

export default function PatientCard({ patient }) {
  const initial = patient.display_id.replace(/[^a-z0-9]/gi, '').slice(-1).toUpperCase()
  return (
    <Link className="patient-card" to={`/patients/${patient.id}`}>
      <div className="patient-card-heading">
        <span className="patient-avatar">{initial}</span>
        <div>
        <span className="eyebrow">Patient</span>
        <h2>{patient.display_id}</h2>
        {patient.full_name && <p className="muted">{patient.full_name}</p>}
        </div>
      </div>
      <div className="patient-meta">
        <span>{patient.session_count} sessions</span>
        <span>{patient.last_session_date || 'No sessions yet'}</span>
      </div>
    </Link>
  )
}

import { Link } from 'react-router-dom'

export default function PatientCard({ patient }) {
  return (
    <Link className="patient-card" to={`/patients/${patient.id}`}>
      <div>
        <span className="eyebrow">Patient</span>
        <h2>{patient.display_id}</h2>
      </div>
      <div className="patient-meta">
        <span>{patient.session_count} sessions</span>
        <span>{patient.last_session_date || 'No sessions yet'}</span>
      </div>
    </Link>
  )
}

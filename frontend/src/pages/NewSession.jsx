import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { listPatients } from '../services/patients'
import { createSession, uploadSessionVideo } from '../services/sessions'

function today() {
  return new Date().toISOString().slice(0, 10)
}

export default function NewSession() {
  const navigate = useNavigate()
  const [patients, setPatients] = useState([])
  const [patientId, setPatientId] = useState('')
  const [sessionDate, setSessionDate] = useState(today)
  const [sessionType, setSessionType] = useState('therapy')
  const [notes, setNotes] = useState('')
  const [video, setVideo] = useState(null)
  const [consent, setConsent] = useState(false)
  const [progress, setProgress] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    listPatients().then((data) => {
      setPatients(data)
      if (data[0]) setPatientId(String(data[0].id))
    }).catch((err) => setError(err.message))
  }, [])

  async function submit(event) {
    event.preventDefault()
    if (!consent || !video) return
    setBusy(true)
    setError('')
    try {
      const session = await createSession({
        patient_id: Number(patientId),
        session_date: sessionDate,
        session_type: sessionType,
        consent_confirmed: consent,
        notes: notes || null,
      })
      await uploadSessionVideo(session.id, video, setProgress)
      navigate(`/sessions/${session.id}`)
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return <main className="page">
    <Link className="back-link" to="/patients">← Patients</Link>
    <header className="page-header"><div><span className="eyebrow">Session intake</span><h1>New session</h1></div></header>
    <form className="form-card" onSubmit={submit}>
      {patients.length === 0 && <p className="muted">Create a patient before starting a session.</p>}
      <label>Patient<select value={patientId} onChange={(event) => setPatientId(event.target.value)} required disabled={patients.length === 0}>
        {patients.map((patient) => <option key={patient.id} value={patient.id}>{patient.display_id}</option>)}
      </select></label>
      <label>Session date<input type="date" value={sessionDate} onChange={(event) => setSessionDate(event.target.value)} required /></label>
      <label>Session type<select value={sessionType} onChange={(event) => setSessionType(event.target.value)}>
        <option value="therapy">Therapy</option><option value="assessment">Assessment</option><option value="intake">Intake</option><option value="follow_up">Follow-up</option>
      </select></label>
      <label>Video file<input type="file" accept="video/*,.mp4,.mov,.avi,.webm,.mkv" onChange={(event) => setVideo(event.target.files[0] || null)} required /></label>
      <label>Notes<textarea rows="4" value={notes} onChange={(event) => setNotes(event.target.value)} /></label>
      <label className="consent-gate"><input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} /><span>I confirm that consent has been obtained for this recording and analysis.</span></label>
      {busy && <div className="upload-progress"><div className="progress-track"><div style={{ width: `${progress}%` }} /></div><span>{progress}% uploaded</span></div>}
      {error && <p className="error">{error}</p>}
      <button className="button primary" disabled={busy || !consent || !video || patients.length === 0}>{busy ? 'Uploading...' : 'Create session'}</button>
    </form>
  </main>
}

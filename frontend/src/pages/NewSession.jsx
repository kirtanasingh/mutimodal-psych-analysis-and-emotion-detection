import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { listPatients } from '../services/patients'
import { createSession, uploadSessionVideo } from '../services/sessions'

function today() {
  return new Date().toISOString().slice(0, 10)
}

export default function NewSession() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [patients, setPatients] = useState([])
  const [patientId, setPatientId] = useState('')
  const [sessionDate, setSessionDate] = useState(today)
  const [sessionType, setSessionType] = useState('therapy')
  const [notes, setNotes] = useState('')
  const [video, setVideo] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [consent, setConsent] = useState(false)
  const [progress, setProgress] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    listPatients().then((data) => {
      setPatients(data)
      const requestedPatient = searchParams.get('patient')
      if (requestedPatient && data.some((patient) => String(patient.id) === requestedPatient)) {
        setPatientId(requestedPatient)
      } else {
        setPatientId('')
      }
    }).catch((err) => setError(err.message))
  }, [searchParams])

  async function submit(event) {
    event.preventDefault()
    if (!patientId) {
      setError('Select an existing patient before creating a session.')
      return
    }
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
    <form className="form-card session-form" onSubmit={submit}>
      <div className="form-stepper"><span className="step-active">1 <b>Session details</b></span><i /><span>2 <b>Upload recording</b></span><i /><span>3 <b>Analysis</b></span></div>
      {patients.length === 0 && <p className="error">Create a patient in the Patients section before starting a session.</p>}
      {patients.length > 0 && !patientId && <p className="error">Select a patient before uploading a session for analysis.</p>}
      <label>Patient<select value={patientId} onChange={(event) => setPatientId(event.target.value)} required disabled={patients.length === 0}>
        {patients.map((patient) => <option key={patient.id} value={patient.id}>{patient.display_id}</option>)}
      </select></label>
      <label>Session date<input type="date" value={sessionDate} onChange={(event) => setSessionDate(event.target.value)} required /></label>
      <label>Session type<select value={sessionType} onChange={(event) => setSessionType(event.target.value)}>
        <option value="therapy">Therapy</option><option value="assessment">Assessment</option><option value="intake">Intake</option><option value="follow_up">Follow-up</option>
      </select></label>
      <label className={`dropzone ${dragging ? 'dragging' : ''}`} onDragOver={(event) => { event.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); setVideo(event.dataTransfer.files[0] || null) }}><input type="file" accept="video/*,.mp4,.mov,.avi,.webm,.mkv" onChange={(event) => setVideo(event.target.files[0] || null)} required /><strong>{video ? video.name : 'Drop a session video here'}</strong><span>{video ? `${Math.round(video.size / 1024 / 1024 * 10) / 10} MB ready to upload` : 'or click to browse · MP4, MOV, AVI, WEBM'}</span></label>
      <label>Notes<textarea rows="4" value={notes} onChange={(event) => setNotes(event.target.value)} /></label>
      <label className="consent-gate"><input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} /><span>I confirm that consent has been obtained for this recording and analysis.</span></label>
      {busy && <div className="upload-progress"><div className="progress-track"><div style={{ width: `${progress}%` }} /></div><span>{progress}% uploaded</span><div className="upload-steps"><span className="step-done">✓ Details</span><span className="step-active">◌ Uploading</span><span>○ Processing</span></div></div>}
      {error && <p className="error">{error}</p>}
      <button className="button primary" disabled={busy || !consent || !video || patients.length === 0}>{busy ? 'Uploading...' : 'Create session'}</button>
    </form>
  </main>
}

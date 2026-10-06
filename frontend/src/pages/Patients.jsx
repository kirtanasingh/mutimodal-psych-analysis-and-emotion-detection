import { useEffect, useState } from 'react'
import PatientCard from '../components/PatientCard'
import { createPatient, listPatients } from '../services/patients'

export default function Patients() {
  const [patients, setPatients] = useState([])
  const [open, setOpen] = useState(false)
  const [ageRange, setAgeRange] = useState('')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState('')

  async function refresh() {
    try {
      setPatients(await listPatients())
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    let cancelled = false
    listPatients()
      .then((data) => {
        if (!cancelled) setPatients(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
    return () => { cancelled = true }
  }, [])

  async function submit(event) {
    event.preventDefault()
    try {
      await createPatient({ basic_info_json: { age_range: ageRange, notes } })
      setAgeRange('')
      setNotes('')
      setOpen(false)
      setError('')
      await refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <main className="page">
      <header className="page-header">
        <div><span className="eyebrow">Care management</span><h1>Patients</h1></div>
        <button className="button primary" onClick={() => setOpen(true)}>+ New Patient</button>
      </header>
      {error && <p className="error">{error}</p>}
      {patients.length === 0 ? <div className="empty-state">No patients yet. Add your first patient to begin.</div> : (
        <div className="patient-grid">{patients.map((patient) => <PatientCard key={patient.id} patient={patient} />)}</div>
      )}
      {open && <div className="modal-backdrop"><form className="modal" onSubmit={submit}>
        <h2>New patient</h2>
        <p className="muted">Optional information only. No legal name is required.</p>
        <label>Age range<input value={ageRange} onChange={(event) => setAgeRange(event.target.value)} placeholder="25-34" /></label>
        <label>Notes<textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows="4" /></label>
        <div className="modal-actions"><button type="button" className="button" onClick={() => setOpen(false)}>Cancel</button><button className="button primary">Create patient</button></div>
      </form></div>}
    </main>
  )
}

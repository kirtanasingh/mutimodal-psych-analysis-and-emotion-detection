import { useEffect, useState } from 'react'
import PatientCard from '../components/PatientCard'
import { createPatient, listPatients } from '../services/patients'

export default function Patients() {
  const [patients, setPatients] = useState([])
  const [open, setOpen] = useState(false)
  const [fullName, setFullName] = useState('')
  const [age, setAge] = useState('')
  const [profession, setProfession] = useState('')
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
    if (!fullName.trim() && !age && !profession.trim() && !ageRange.trim() && !notes.trim()) {
      setError('Enter at least one patient detail before creating a patient.')
      return
    }
    try {
      await createPatient({ full_name: fullName || null, age: age ? Number(age) : null, profession: profession || null, basic_info_json: { age_range: ageRange, notes } })
      setFullName('')
      setAge('')
      setProfession('')
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
      {open && <div className="modal-backdrop" role="dialog" aria-modal="true"><form className="modal" onSubmit={submit}>
        <h2>New patient</h2>
        <p className="muted">Optional information only. No legal name is required.</p>
        <label>Full name<input value={fullName} onChange={(event) => setFullName(event.target.value)} /></label>
        <label>Age<input type="number" min="0" value={age} onChange={(event) => setAge(event.target.value)} /></label>
        <label>Profession<input value={profession} onChange={(event) => setProfession(event.target.value)} /></label>
        <label>Age range<input value={ageRange} onChange={(event) => setAgeRange(event.target.value)} placeholder="25-34" /></label>
        <label>Notes<textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows="4" /></label>
        <div className="modal-actions"><button type="button" className="button" onClick={() => setOpen(false)}>Cancel</button><button className="button primary">Create patient</button></div>
      </form></div>}
    </main>
  )
}

import { useEffect, useState } from 'react'
import { Download, FileText } from 'lucide-react'
import { downloadSessionReport } from '../services/sessions'
import { getRecentReports } from '../services/dashboard'

function formatDate(value) {
  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(`${value}T00:00:00`))
}

export default function Reports() {
  const [reports, setReports] = useState([])
  const [error, setError] = useState('')
  const [downloading, setDownloading] = useState(null)

  useEffect(() => {
    getRecentReports().then(setReports).catch((err) => setError(err.message))
  }, [])

  async function download(report) {
    setDownloading(report.session_id)
    try {
      const blob = await downloadSessionReport(report.session_id)
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = `session-${report.session_id}-analysis.pdf`
      anchor.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err.message)
    } finally {
      setDownloading(null)
    }
  }

  return <main className="page">
    <header className="page-header"><div><span className="eyebrow">Documentation</span><h1>Reports</h1><p className="muted">Generated session reports ready for professional review.</p></div><FileText size={22} className="panel-muted" /></header>
    {error && <p className="error">{error}</p>}
    {reports.length === 0 ? <div className="empty-state"><h2>No reports generated yet</h2><p>Reports will appear here after a session is complete.</p></div> : <section className="panel"><div className="data-list">{reports.map((report) => <div className="data-row" key={report.id}><div><strong>{report.patient_display_id}</strong><span>Session {formatDate(report.session_date)} · Generated {new Date(report.generated_at).toLocaleString()}</span></div><button className="button small" onClick={() => download(report)} disabled={downloading === report.session_id}><Download size={14} />{downloading === report.session_id ? 'Preparing...' : 'Download'}</button></div>)}</div></section>}
  </main>
}

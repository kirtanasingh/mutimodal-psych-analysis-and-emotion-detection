import { useEffect, useState } from 'react'
import { ArrowUpRight, Clock3, FileText, Users, Activity } from 'lucide-react'
import { Link } from 'react-router-dom'
import { getDashboardSummary, getRecentReports, getRecentSessions, getPriorityQueue, getCaseloadSnapshot } from '../services/dashboard'
import { useAuth } from '../context/AuthContext'
import { downloadSessionReport } from '../services/sessions'
import PriorityQueue from '../components/PriorityQueue'
import CaseloadSnapshot from '../components/CaseloadSnapshot'

function formatDate(value) { return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(`${value}T00:00:00`)) }

export default function Dashboard() {
  const { user } = useAuth()
  const [data, setData] = useState({ summary: null, sessions: [], reports: [] })
  const [error, setError] = useState('')
  const [downloading, setDownloading] = useState(null)
  const [priorityQueue, setPriorityQueue] = useState([])
  const [caseload, setCaseload] = useState(null)
  const [showRecent, setShowRecent] = useState(false)
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
    } catch (err) { setError(err.message) } finally { setDownloading(null) }
  }

  useEffect(() => {
    Promise.all([getDashboardSummary(), getRecentSessions(), getRecentReports(), getPriorityQueue(), getCaseloadSnapshot()])
      .then(([summary, sessions, reports, queue, snapshot]) => { setData({ summary, sessions, reports }); setPriorityQueue(queue); setCaseload(snapshot) })
      .catch((err) => setError(err.message))
  }, [])
  const stats = data.summary ? [
    ['Total patients', data.summary.total_patients, Users, 'patients'],
    ['Sessions this week', data.summary.sessions_this_week, Activity, 'sessions'],
    ['Awaiting review', data.summary.reports_awaiting_review, FileText, 'reports'],
    ['In processing', data.summary.sessions_processing, Clock3, 'pending'],
  ] : []
  return <main className="page">
    <header className="page-header dashboard-header"><div><span className="eyebrow">Overview</span><h1>Good morning{user?.display_name ? `, ${user.display_name.split(' ')[0]}` : ''}</h1><p className="muted">A calm view of your clinical workspace.</p></div><Link className="button primary" to="/sessions/new">New session <ArrowUpRight size={16} /></Link></header>
    {error && <p className="error">{error}</p>}
    <div className="stat-grid">{stats.map(([label, value, Icon, tone]) => <div className="stat-card" key={label}><div className={`stat-icon ${tone}`}><Icon size={18} /></div><p>{label}</p><strong>{value}</strong></div>)}</div>
    <CaseloadSnapshot snapshot={caseload} />
    <div className="dashboard-stack">
      <PriorityQueue sessions={priorityQueue} recentSessions={data.sessions} showRecent={showRecent} onToggle={() => setShowRecent((value) => !value)} />
      <section className="panel"><div className="panel-heading"><div><span className="eyebrow">Documentation</span><h2>Reports</h2></div><FileText size={18} className="panel-muted" /></div>
        {data.reports.length === 0 ? <Empty text="No reports generated yet." /> : <div className="data-list">{data.reports.map((report) => <div className="data-row" key={report.id}><div><strong>{report.patient_display_id}</strong><span>{formatDate(report.session_date)}</span></div>{report.pdf_available ? <button className="button small" onClick={() => download(report)} disabled={downloading === report.session_id}>{downloading === report.session_id ? 'Preparing...' : 'Download'}</button> : <span className="muted">Draft</span>}</div>)}</div>}
      </section>
    </div>
  </main>
}

function Empty({ text }) { return <div className="panel-empty"><FileText size={22} /><p>{text}</p></div> }

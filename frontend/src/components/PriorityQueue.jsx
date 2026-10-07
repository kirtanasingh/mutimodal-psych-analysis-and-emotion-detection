import { Link } from 'react-router-dom'
import SessionFingerprint from './SessionFingerprint'

function formatDate(value) {
  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(`${value}T00:00:00`))
}

export default function PriorityQueue({ sessions, recentSessions, showRecent, onToggle }) {
  const rows = showRecent ? recentSessions : sessions
  return <section className="panel priority-panel">
    <div className="panel-heading">
      <div><span className="eyebrow">Review workflow</span><h2>{showRecent ? 'Recent sessions' : 'Priority review queue'}</h2></div>
      <button className="button small" onClick={onToggle}>{showRecent ? 'View priority queue' : 'View all recent sessions'}</button>
    </div>
    {rows.length === 0 ? <div className="panel-empty"><p>{showRecent ? 'No sessions yet.' : 'No sessions awaiting review.'}</p></div> : <div className="data-list">{rows.map((session) => {
      const highPriority = !showRecent && session.urgency_score >= 3
      return <Link className="data-row priority-row" to={`/sessions/${session.id}`} key={session.id}>
        <span className={`urgency-dot ${highPriority ? 'high' : 'medium'}`} />
        <div className="priority-main"><strong>{session.patient_display_id}</strong><span>{formatDate(session.session_date)}{session.duration_seconds ? ` · ${Math.round(session.duration_seconds / 60)} min` : ''}</span>{!showRecent && <div className="reason-tags">{session.reason_tags.map((tag) => <span className="reason-tag" key={tag}>{tag}</span>)}</div>}</div>
        <SessionFingerprint distribution={session.emotion_distribution} />
        {!showRecent && <strong className="urgency-score">{session.urgency_score}</strong>}
      </Link>
    })}</div>}
  </section>
}

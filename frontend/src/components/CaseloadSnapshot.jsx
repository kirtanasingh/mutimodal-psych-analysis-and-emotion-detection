import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { EMOTION_COLORS } from '../constants/emotionColors'

export default function CaseloadSnapshot({ snapshot }) {
  const data = Object.keys(EMOTION_COLORS).map((emotion) => ({
    emotion,
    probability: snapshot?.emotion_distribution?.[emotion] || 0,
  }))
  return <section className="visual-card caseload-snapshot">
    <span className="eyebrow">Aggregate view</span>
    <h2>Caseload signal snapshot</h2>
    <p className="muted">Last {snapshot?.period_days || 7} days, {snapshot?.session_count || 0} sessions, aggregated and anonymized.</p>
    <div className="rechart-wrap compact"><ResponsiveContainer width="100%" height={220}><BarChart data={data} layout="vertical" margin={{ left: 8, right: 18, top: 8, bottom: 8 }}><CartesianGrid horizontal={false} stroke="#e2e8f0" /><XAxis type="number" domain={[0, 1]} tickFormatter={(value) => `${Math.round(value * 100)}%`} tick={{ fontSize: 10, fill: '#64748b' }} /><YAxis type="category" dataKey="emotion" width={58} tick={{ fontSize: 10, fill: '#475569' }} /><Tooltip formatter={(value) => `${Math.round(value * 100)}%`} /><Bar dataKey="probability" fill="#0d9488" radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer></div>
  </section>
}

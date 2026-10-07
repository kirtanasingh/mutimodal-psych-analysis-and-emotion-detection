import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { EMOTION_COLORS } from '../constants/emotionColors'

export default function EmotionDistribution({ timeline = [], distribution }) {
  const data = Object.keys(EMOTION_COLORS).map((emotion) => ({ emotion, probability: distribution?.[emotion] ?? (timeline.reduce((sum, row) => sum + (row.probabilities[emotion] || 0), 0) / Math.max(timeline.length, 1)), fill: EMOTION_COLORS[emotion] })).sort((a, b) => b.probability - a.probability)
  const top = data[0]
  return <section className="visual-card chart-card"><span className="eyebrow">Session-wide signal</span><h2>Emotion distribution</h2><div className="rechart-wrap compact"><ResponsiveContainer width="100%" height={250}><BarChart data={data} layout="vertical" margin={{ left: 8, right: 18, top: 8, bottom: 8 }}><CartesianGrid horizontal={false} stroke="#e2e8f0" /><XAxis type="number" domain={[0, 1]} tickFormatter={(value) => `${Math.round(value * 100)}%`} tick={{ fontSize: 10, fill: '#64748b' }} /><YAxis type="category" dataKey="emotion" width={58} tick={{ fontSize: 10, fill: '#475569' }} /><Tooltip formatter={(value) => `${Math.round(value * 100)}%`} /><Bar dataKey="probability" radius={[0, 4, 4, 0]} fill="#0d9488" /></BarChart></ResponsiveContainer></div>{top && <div className="highlight-stat"><span>Most prominent signal</span><strong>{top.emotion}</strong><b>{Math.round(top.probability * 100)}%</b></div>}</section>
}

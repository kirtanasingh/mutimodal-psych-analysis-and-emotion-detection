import { useMemo } from 'react'
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { EMOTION_COLORS, EMOTION_LABELS } from '../constants/emotionColors'

const formatTime = (seconds) => `${Math.floor(seconds / 60)}:${Math.floor(seconds % 60).toString().padStart(2, '0')}`

export default function EmotionTimeline({ timeline, onSelect }) {
  const data = useMemo(() => timeline.map((window) => ({ ...window, time: formatTime(window.window_start) })), [timeline])
  return <section className="visual-card chart-card"><div className="visual-heading"><div><span className="eyebrow">Fused signal</span><h2>Emotion timeline</h2><p className="chart-help">Click a point to inspect the window’s modality signals.</p><p className="chart-help">Lighter segments indicate lower model confidence.</p></div></div><div className="rechart-wrap"><ResponsiveContainer width="100%" height={310}><LineChart data={data} onClick={(event) => event?.activePayload?.[0] && onSelect?.(event.activePayload[0].payload)} margin={{ top: 10, right: 15, left: -18, bottom: 8 }}><CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" /><XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} /><YAxis domain={[0, 1]} tickFormatter={(value) => `${Math.round(value * 100)}%`} tick={{ fontSize: 10, fill: '#64748b' }} /><Tooltip formatter={(value) => `${Math.round(value * 100)}%`} labelFormatter={(label) => `Window ${label}`} /><Legend wrapperStyle={{ fontSize: 11 }} />{EMOTION_LABELS.map((emotion) => <Line key={emotion} type="monotone" dataKey={`probabilities.${emotion}`} name={emotion} stroke={EMOTION_COLORS[emotion]} strokeWidth={2} dot={<ConfidenceDot />} activeDot={{ r: 5 }} />)}</LineChart></ResponsiveContainer></div></section>
}

function ConfidenceDot({ cx, cy, payload, stroke }) {
  return <circle cx={cx} cy={cy} r={2.5} fill={stroke} opacity={payload?.confidence < 0.4 ? 0.4 : 1} />
}

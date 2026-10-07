import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer, Tooltip } from 'recharts'
import { EMOTION_COLORS } from '../constants/emotionColors'

export default function SessionFingerprint({ distribution = {} }) {
  const data = Object.keys(EMOTION_COLORS).map((emotion) => ({
    emotion,
    probability: Number(distribution[emotion] || 0),
  }))
  return <div className="session-fingerprint" title="Session emotion fingerprint">
    <ResponsiveContainer width="100%" height="100%">
      <RadarChart data={data} outerRadius="72%">
        <PolarGrid stroke="#cbd5e1" />
        <PolarAngleAxis dataKey="emotion" tick={false} />
        <Radar dataKey="probability" stroke="#0d9488" fill="#0d9488" fillOpacity={0.22} strokeWidth={1.5} />
        <Tooltip formatter={(value) => `${Math.round(value * 100)}%`} />
      </RadarChart>
    </ResponsiveContainer>
  </div>
}

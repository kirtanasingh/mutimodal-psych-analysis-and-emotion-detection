import { EMOTION_COLORS } from '../constants/emotionColors'

export default function ModalityComparison({ selected, analysis }) {
  if (!selected) return <section className="visual-card chart-card"><span className="eyebrow">Window detail</span><h2>Modality comparison</h2><p className="muted">Complete analysis to compare model signals.</p></section>
  const matching = analysis.find((row) => row.window_start === selected.window_start) || {}
  return <section className="visual-card chart-card"><div className="visual-heading"><div><span className="eyebrow">Window {formatTime(selected.window_start)}</span><h2>Modality comparison</h2><p className="chart-help">Lighter segments indicate lower model confidence.</p></div></div><div className="fusion-result"><span>Combined / fusion</span><strong>{selected.dominant_emotion}</strong><b>{Math.round(selected.confidence * 100)}%</b></div><div className="modality-bars">{['text', 'audio', 'face'].map((modality) => { const result = matching[modality]; return <div className="modality-bar-row" key={modality}><span>{modality}</span><div><i style={{ width: `${result ? result.confidence * 100 : 0}%`, opacity: result && result.confidence < 0.4 ? 0.4 : 1, background: result ? EMOTION_COLORS[result.dominant_emotion] : '#cbd5e1' }} /></div><b>{result ? `${result.dominant_emotion} ${Math.round(result.confidence * 100)}%` : 'No face'}</b></div> })}</div></section>
}

function formatTime(seconds) { return `${Math.floor(seconds / 60)}:${Math.floor(seconds % 60).toString().padStart(2, '0')}` }

export default function TranscriptPanel({ transcript }) {
  return <details className="transcript-details" open><summary>Transcript{transcript?.language ? ` · ${transcript.language}` : ''}</summary><div className="transcript-list">{!transcript?.segments?.length ? <p className="muted">No speech segments detected.</p> : transcript.segments.map((segment) => <div className="transcript-segment" key={segment.id}><span className="transcript-time">{formatTime(segment.start_time)}</span><span>{segment.text}</span></div>)}</div></details>
}
function formatTime(seconds) { return `${Math.floor(seconds / 60)}:${Math.floor(seconds % 60).toString().padStart(2, '0')}` }

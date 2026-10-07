export default function DivergenceStrip({ timeline, divergences, onSelect }) {
  const byWindow = new Map((divergences || []).map((item) => [`${item.window_start}-${item.window_end}`, item]))
  return <div className="divergence-strip" aria-label="Cross-modal divergence indicators">
    {timeline.map((window) => {
      const item = byWindow.get(`${window.window_start}-${window.window_end}`)
      return <button
        key={`${window.window_start}-${window.window_end}`}
        className={`divergence-segment ${item ? 'divergent' : ''}`}
        title={item?.description || 'No cross-modal divergence detected'}
        onClick={() => item && onSelect?.(window)}
        aria-label={item ? item.description : 'No divergence'}
      />
    })}
  </div>
}

import { useEffect, useState } from 'react'

const STEPS = [
  { icon: '🔍', label: 'Extracting input features…' },
  { icon: '🧠', label: 'Running AI fraud detection model…' },
  { icon: '📊', label: 'Computing risk score & confidence…' },
  { icon: '🔐', label: 'Generating security recommendations…' },
  { icon: '💾', label: 'Saving analysis to database…' },
]

export default function LoadingOverlay({ active }) {
  const [stepIdx, setStepIdx] = useState(0)
  const [done, setDone] = useState([])

  useEffect(() => {
    if (!active) { setStepIdx(0); setDone([]); return }
    let i = 0
    const tick = () => {
      if (i > 0) setDone(d => [...d, i - 1])
      setStepIdx(i)
      i++
      if (i < STEPS.length) setTimeout(tick, 900 + Math.random() * 400)
    }
    const t = setTimeout(tick, 300)
    return () => clearTimeout(t)
  }, [active])

  if (!active) return null

  return (
    <div className="loading-overlay">
      {/* Spinning ring */}
      <div className="loader-ring">
        <svg viewBox="0 0 130 130">
          <circle className="gauge-track" cx="65" cy="65" r="56" strokeWidth="10"/>
          <circle cx="65" cy="65" r="56" fill="none" strokeWidth="10"
            stroke="#7c3aed" strokeLinecap="round"
            strokeDasharray="352" strokeDashoffset="120"
            style={{ animation: 'spin 1.5s linear infinite', transformOrigin: 'center' }}/>
          <circle cx="65" cy="65" r="40" fill="none" strokeWidth="6"
            stroke="#06b6d4" strokeLinecap="round"
            strokeDasharray="251" strokeDashoffset="100"
            style={{ animation: 'spin 2s linear infinite reverse', transformOrigin: 'center' }}/>
        </svg>
        <div className="loader-icon">🧠</div>
      </div>

      <div className="loading-title">AI Fraud Detection in Progress</div>
      <div className="loading-sub">Our model is deeply analyzing your submission…</div>

      <div className="loading-steps">
        {STEPS.map((s, i) => (
          <div key={i} className={`load-step ${done.includes(i) ? 'done' : i === stepIdx ? 'active' : ''}`}>
            <span>{done.includes(i) ? '✓' : s.icon}</span>
            <span>{s.label}</span>
          </div>
        ))}
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

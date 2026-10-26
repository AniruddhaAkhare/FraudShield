import { useEffect, useState } from 'react'

const STEPS = [
  { icon: '🔍', label: 'Extracting audio waveforms & features…' },
  { icon: '⚡', label: 'Running speech recognition & acoustic classification…' },
  { icon: '📊', label: 'Applying Multimodal Risk Fusion…' },
  { icon: '🔐', label: 'Generating security recommendations…' },
  { icon: '💾', label: 'Saving analysis to database…' },
]

export default function LoadingOverlay({ active }) {
  const [stepIdx, setStepIdx] = useState(0)
  const [done, setDone] = useState([])
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    if (!active) {
      setStepIdx(0)
      setDone([])
      setElapsed(0)
      return
    }

    const timer = setInterval(() => {
      setElapsed(e => e + 1)
    }, 1000)

    let i = 0
    let stepTimer = null

    const tick = () => {
      setDone(d => (i > 0 && !d.includes(i - 1) ? [...d, i - 1] : d))
      setStepIdx(i)
      i++
      if (i < STEPS.length) {
        stepTimer = setTimeout(tick, 1000 + Math.random() * 400)
      } else {
        // Complete the final step after a short moment
        stepTimer = setTimeout(() => {
          setDone(d => [...new Set([...d, STEPS.length - 1])])
        }, 1200)
      }
    }

    stepTimer = setTimeout(tick, 300)

    return () => {
      clearInterval(timer)
      if (stepTimer) clearTimeout(stepTimer)
    }
  }, [active])

  if (!active) return null

  return (
    <div className="loading-overlay">
      {/* Spinning ring */}
      <div className="loader-ring">
        <svg viewBox="0 0 130 130">
          <circle className="gauge-track" cx="65" cy="65" r="56" strokeWidth="10"/>
          <circle cx="65" cy="65" r="56" fill="none" strokeWidth="10"
            stroke="#ec4899" strokeLinecap="round"
            strokeDasharray="352" strokeDashoffset="120"
            style={{ animation: 'spin 1.5s linear infinite', transformOrigin: 'center' }}/>
          <circle cx="65" cy="65" r="40" fill="none" strokeWidth="6"
            stroke="#06b6d4" strokeLinecap="round"
            strokeDasharray="251" strokeDashoffset="100"
            style={{ animation: 'spin 2s linear infinite reverse', transformOrigin: 'center' }}/>
        </svg>
        <div className="loader-icon">🛡️</div>
      </div>

      <div className="loading-title">Fraud Detection in Progress</div>
      <div className="loading-sub">
        {elapsed > 6
          ? 'Transcribing audio conversation & verifying social engineering tactics…'
          : 'Running feature extraction, classification & multimodal risk fusion…'}
      </div>

      <div className="loading-steps">
        {STEPS.map((s, i) => (
          <div key={i} className={`load-step ${done.includes(i) ? 'done' : i === stepIdx ? 'active' : ''}`}>
            <span>{done.includes(i) ? '✓' : s.icon}</span>
            <span>{s.label}</span>
          </div>
        ))}
      </div>

      {elapsed > 10 && (
        <div style={{ marginTop: 14, fontSize: '0.82rem', color: 'rgba(255,255,255,0.6)', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ animation: 'pulse 1.2s infinite' }}>⏳</span>
          <span>Audio transcription in progress ({elapsed}s elapsed) — finalizing report…</span>
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

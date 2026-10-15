import { useEffect, useRef, useState } from 'react'

const RISK_COLORS = {
  CRITICAL: '#ef4444',
  HIGH:     '#f97316',
  MEDIUM:   '#eab308',
  LOW:      '#22c55e',
}

export default function RiskGauge({ score, level, confidence, scamType }) {
  const fillRef  = useRef(null)
  const [confW, setConfW] = useState(0)
  const circumference = 2 * Math.PI * 54  // r = 54

  useEffect(() => {
    if (!fillRef.current) return
    fillRef.current.style.strokeDasharray  = circumference
    fillRef.current.style.strokeDashoffset = circumference
    fillRef.current.style.stroke = RISK_COLORS[level] || '#7c3aed'
    setTimeout(() => {
      if (fillRef.current) {
        fillRef.current.style.strokeDashoffset = circumference - (score / 100) * circumference
      }
    }, 200)
    setTimeout(() => setConfW(confidence), 400)
  }, [score, level, confidence])

  return (
    <div className="risk-gauge">
      <div className="gauge-ring">
        <svg viewBox="0 0 120 120">
          <circle className="gauge-track" cx="60" cy="60" r="54"/>
          <circle ref={fillRef} className="gauge-fill" cx="60" cy="60" r="54"
            strokeDasharray={circumference} strokeDashoffset={circumference}/>
        </svg>
        <div className="gauge-center">
          <div className="gauge-score" style={{ color: RISK_COLORS[level] || '#7c3aed' }}>
            {Math.round(score)}
          </div>
          <div className="gauge-label">/ 100</div>
        </div>
      </div>

      <span className={`risk-badge ${level}`}>{level}</span>

      <div className="conf-wrap">
        <div className="conf-top">
          <span>Confidence Score</span>
          <span>{Math.round(confidence)}%</span>
        </div>
        <div className="conf-track">
          <div className="conf-fill" style={{ width: `${confW}%` }}/>
        </div>
      </div>

      <div style={{ marginTop: '1rem', padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-subtle)' }}>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px' }}>
          Classification
        </div>
        <div style={{ fontSize: '0.88rem', fontWeight: 600 }}>{scamType}</div>
      </div>
    </div>
  )
}

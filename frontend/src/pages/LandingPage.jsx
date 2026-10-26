import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchStats } from '../api/client.js'

const SCAM_TAGS = [
  ['🎣','Phishing Attack'], ['💰','Financial Scam'], ['🪪','Identity Theft'],
  ['🏛️','Fake Authority'], ['🎰','Lottery / Prize Scam'], ['📈','Investment Fraud'],
  ['💕','Romance Scam'],   ['💻','Tech Support Scam'],  ['💼','Employment Scam'],
  ['🎨','Synthetic / Forged Media'], ['🦠','Malware / Ransomware'], ['📋','Counterfeit Document'],
]

const FEATURES = [
  { icon: '📊', bg: 'fi-purple', span: 7, title: 'On-Screen Risk Assessment',
    desc: 'Instant visual risk score (0–100), color-coded risk level (LOW → CRITICAL), scam classification, and model confidence — displayed in a stunning bento dashboard.',
    extra: (
      <div style={{ display:'flex', gap:8, flexWrap:'wrap', marginTop:'1.2rem' }}>
        {['CRITICAL','HIGH','MEDIUM','LOW'].map(l => (
          <span key={l} className={`risk-badge ${l}`}>{l}</span>
        ))}
      </div>
    )
  },
  { icon: '⚠️', bg: 'fi-red',    span: 5, title: 'Detection Analysis',      desc: 'Identifies suspicious URLs, threatening language, fake authority claims, visual inconsistencies, and social engineering tactics with severity ratings.' },
  { icon: '🧾', bg: 'fi-cyan',   span: 4, title: 'Evidence Extraction',     desc: 'Extracted text, URL metadata, QR decoded data, and key visual or document findings.' },
  { icon: '🔒', bg: 'fi-green',  span: 4, title: 'Security Recommendations', desc: 'Actionable steps: avoid links, verify sender, report to authorities, enable 2FA, and more.' },
  { icon: '📄', bg: 'fi-pink',   span: 4, title: 'PDF Report Download',     desc: 'Downloadable branded PDF with full evidence, indicators, risk score, and recommendations.' },
]

const INPUT_TYPES = [
  { icon: '💬', type: 'text',  label: 'Text & Messages',    model: 'BERT',
    desc: 'Analyses messages, emails, and extracted text to detect scam language, impersonation, threats, urgency, and fraudulent requests.' },
  { icon: '🔗', type: 'url',   label: 'URLs & Links',       model: 'XGBoost',
    desc: 'Classifies URLs using features such as URL length, domain structure, suspicious characters, and other URL indicators.' },
  { icon: '🖼️', type: 'image', label: 'Images & Screenshots', model: 'Vision Transformer (ViT) + OCR',
    desc: 'Analyses screenshots and images for visual impersonation patterns via ViT; OCR extracts text so it can be analysed by BERT.' },
  { icon: '📱', type: 'qr',    label: 'QR Codes',           model: 'QR Code Decoding',
    desc: 'Extracts URLs or text from QR codes and routes the content to the appropriate detection module.' },
  { icon: '🎙️', type: 'audio', label: 'Call Recordings',   model: 'Speech Acoustic Pipeline',
    desc: 'Evaluates phone calls for digital arrest extortion, fake police/CBI threats, bank KYC vishing, and synthetic AI voice cloning.' },
]

const STEPS = [
  { n:'1', title:'Select Input Type',      desc:'Choose from text, URL, image, QR code, or call audio recording.' },
  { n:'2', title:'Submit Evidence',        desc:'Paste message/URL, or upload your document/image/call recording.' },
  { n:'3', title:'Feature Classification', desc:'Dedicated BERT, XGBoost, ViT, QR decoder, or Speech Acoustic Pipeline extracts and evaluates features.' },
  { n:'4', title:'Multimodal Risk Fusion', desc:'Combines outputs from available models into an overall risk score and category.' },
  { n:'5', title:'Download Report',        desc:'Export a professional PDF report for sharing.' },
]

function Particles() {
  const ref = useRef(null)
  useEffect(() => {
    if (!ref.current) return
    const colors = ['#7c3aed','#06b6d4','#10b981','#9d62f5']
    for (let i = 0; i < 22; i++) {
      const p = document.createElement('div')
      p.className = 'particle'
      p.style.cssText = `left:${Math.random()*100}%;width:${Math.random()*3+1}px;height:${Math.random()*3+1}px;background:${colors[Math.floor(Math.random()*colors.length)]};animation-duration:${Math.random()*12+8}s;animation-delay:${Math.random()*8}s;animation-name:floatUp;animation-iteration-count:infinite;`
      ref.current.appendChild(p)
    }
    const style = document.createElement('style')
    style.textContent = `
      .particle{position:absolute;border-radius:50%;opacity:0;animation-timing-function:linear;}
      @keyframes floatUp{0%{transform:translateY(100vh) scale(0);opacity:0}10%{opacity:0.6}90%{opacity:0.2}100%{transform:translateY(-10vh) scale(1.5);opacity:0}}
    `
    document.head.appendChild(style)
    return () => style.remove()
  }, [])
  return <div ref={ref} style={{ position:'absolute',inset:0,overflow:'hidden',pointerEvents:'none' }}/>
}

export default function LandingPage() {
  const navigate = useNavigate()
  const [stats, setStats] = useState({ total: 0, fraud: 0, clean: 0, fraud_rate: 0 })

  useEffect(() => {
    fetchStats().then(r => setStats(r.data)).catch(() => {})
  }, [])

  return (
    <>
      {/* ── Hero ── */}
      <section className="hero">
        <div className="hero-bg"/>
        <div className="hero-grid"/>
        <Particles/>
        <div className="hero-content">
          <div className="hero-badge">⚡ Real-Time • Multi-Modal Detection Architecture</div>
          <h1 className="hero-title">Detect Fraud<br/>Before It Strikes</h1>
          <p className="hero-subtitle">
            FraudShield analyzes text messages, URLs, images, QR codes, and voice call recordings using
            BERT, XGBoost, Vision Transformers (ViT), OCR, and Speech Acoustic Pipelines — delivering instant risk scores, detailed threat
            analysis, and actionable security recommendations.
          </p>
          <div className="hero-cta">
            <button className="btn-primary" onClick={() => navigate('/analyze')}>
              🚀 Analyze Now
            </button>
            <a href="#how-it-works" className="btn-secondary">📖 How It Works</a>
          </div>
          <div className="hero-stats">
            {[
              { v: stats.total,      l: 'Analyses Run' },
              { v: stats.fraud,      l: 'Frauds Detected' },
              { v: 5,                l: 'Detection Modules' },
              { v: stats.fraud_rate+'%', l: 'Fraud Rate' },
            ].map(s => (
              <div key={s.l} className="stat-item">
                <div className="stat-value">{s.v}</div>
                <div className="stat-label">{s.l}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Input Types ── */}
      <div style={{ background: 'linear-gradient(180deg,transparent,rgba(124,58,237,0.04),transparent)' }}>
        <div className="section">
          <div className="section-label">⚡ Multi-Modal Architecture</div>
          <h2 className="section-title">Choose Your Input Type</h2>
          <p className="section-subtitle">FraudShield deploys dedicated detection architectures for each input type, combined via Multimodal Risk Fusion.</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '1.25rem', marginTop: '2rem' }}>
            {INPUT_TYPES.map(t => (
              <div key={t.type}
                className="bento-card input-card"
                style={{ cursor: 'pointer', textAlign: 'center' }}
                onClick={() => navigate(`/analyze?type=${t.type}`)}>
                <div className="bento-icon fi-purple" style={{ margin: '0 auto 1rem' }}>{t.icon}</div>
                <h3>{t.label}</h3>
                <p>{t.desc}</p>
                <span className="type-chip">{t.model}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Features Bento ── */}
      <div className="section" id="features">
        <div className="section-label">🔬 Advanced Capabilities</div>
        <h2 className="section-title">What We Detect &amp; Report</h2>
        <div className="bento-grid">
          {FEATURES.map((f, i) => (
            <div key={i} className="bento-card" style={{ gridColumn: `span ${f.span}` }}>
              <div className={`bento-icon ${f.bg}`}>{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
              {f.extra}
            </div>
          ))}
          {/* History full-width card */}
          <div className="bento-card" style={{ gridColumn: 'span 12', background: 'linear-gradient(135deg,rgba(6,182,212,0.08),rgba(13,18,38,1))' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
              <div>
                <div className="bento-icon fi-cyan" style={{ marginBottom: '0.5rem' }}>🕒</div>
                <h3>Analysis History</h3>
                <p style={{ maxWidth: 500 }}>Full searchable and filterable history of all past analyses. Review any previous submission, re-download the PDF report, or compare results.</p>
              </div>
              <button className="btn-secondary" style={{ marginLeft: 'auto' }} onClick={() => navigate('/history')}>
                View History →
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── How It Works ── */}
      <div className="section" id="how-it-works" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="section-label">🔄 Process</div>
        <h2 className="section-title">How FraudShield Works</h2>
        <div className="steps-grid">
          {STEPS.map(s => (
            <div key={s.n} className="bento-card step-card">
              <div className="step-num">{s.n}</div>
              <h3>{s.title}</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{s.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Scam Types ── */}
      <div style={{ background: 'linear-gradient(180deg,transparent,rgba(6,182,212,0.03),transparent)' }}>
        <div className="section">
          <div className="section-label">🎯 Coverage</div>
          <h2 className="section-title">Fraud Types We Detect</h2>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: '2rem' }}>
            {SCAM_TAGS.map(([icon, label]) => (
              <div key={label} className="scam-tag">{icon} {label}</div>
            ))}
          </div>
        </div>
      </div>

      {/* ── CTA ── */}
      <section style={{ padding: '5rem 2rem', textAlign: 'center', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position:'absolute',inset:0,background:'radial-gradient(ellipse 60% 60% at 50% 50%,rgba(124,58,237,0.15),transparent)' }}/>
        <div style={{ position:'relative', zIndex:1, maxWidth:600, margin:'0 auto' }}>
          <h2 style={{ fontSize:'2.5rem', fontWeight:900, marginBottom:'1rem' }}>Ready to Detect Fraud?</h2>
          <p style={{ color:'var(--text-secondary)', marginBottom:'2rem', fontSize:'1.05rem' }}>Start your first analysis in seconds. No account required.</p>
          <button className="btn-primary" style={{ fontSize:'1.1rem', padding:'16px 40px' }}
            onClick={() => navigate('/analyze')}>
            🛡️ Start Free Analysis
          </button>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer style={{ borderTop:'1px solid rgba(255,255,255,0.06)', padding:'2rem', textAlign:'center', color:'var(--text-muted)', fontSize:'0.82rem' }}>
        FraudShield © 2026 — Multimodal Fraud Detection System. Built with React &amp; Flask.
      </footer>
    </>
  )
}

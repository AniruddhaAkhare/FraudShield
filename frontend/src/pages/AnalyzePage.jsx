import { useState, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { analyzeText, analyzeUrl, analyzeImage, analyzeQr, analyzeAudio } from '../api/client.js'
import { useToast } from '../context/ToastContext.jsx'
import LoadingOverlay from '../components/LoadingOverlay.jsx'
import FileDropZone from '../components/FileDropZone.jsx'
import AudioDropZone from '../components/AudioDropZone.jsx'

const TYPES = [
  { key: 'text',  icon: '💬', label: 'Text / Message' },
  { key: 'url',   icon: '🔗', label: 'URL / Link' },
  { key: 'image', icon: '🖼️', label: 'Image / Screenshot' },
  { key: 'qr',    icon: '📱', label: 'QR Code' },
  { key: 'audio', icon: '🎙️', label: 'Call Recording' },
]

const PHISHING_SAMPLE = `URGENT! Your bank account has been temporarily suspended due to suspicious activity. Click the link immediately to restore access: http://secure-banking-verify.tk/restore?id=user123&token=xyz. Failure to verify within 24 hours will result in permanent account closure. — ICICI Bank Security Team`
const LEGIT_SAMPLE    = `Hi! Your order #47821 has been shipped. Track your package at: amazon.in/track/47821. Expected delivery: Tomorrow between 9AM–6PM. — Amazon`

/* ─── Text Panel ── */
function TextPanel({ loading, onSubmit }) {
  const [msg, setMsg] = useState('')
  return (
    <div className="input-panel">
      <div className="panel-title">💬 Text &amp; Message Analysis</div>
      <div className="panel-desc">
        Paste WhatsApp messages, SMS, tweets, emails, or any social media content.
        BERT analyses messages, emails, and extracted text to detect scam language, impersonation, threats, urgency, and fraudulent requests.
      </div>
      <label className="field-label">Message / Content</label>
      <textarea
        rows={10}
        value={msg}
        onChange={e => setMsg(e.target.value)}
        placeholder={`Paste your suspicious message here...\n\nExample: 'URGENT: Your account has been compromised. Click here to verify: http://bit.ly/3abc...'`}
      />
      <div className="sample-btns">
        <button className="sample-btn" onClick={() => setMsg(PHISHING_SAMPLE)}>Try Phishing Sample</button>
        <button className="sample-btn" onClick={() => setMsg(LEGIT_SAMPLE)}>Try Legitimate Sample</button>
      </div>
      <button className="analyze-btn" disabled={loading} onClick={() => onSubmit('text', msg)}>
        {loading ? '⏳ Analyzing…' : '💬 Run BERT Text Detection'}
      </button>
    </div>
  )
}

/* ─── URL Panel ── */
function UrlPanel({ loading, onSubmit }) {
  const [url, setUrl] = useState('')
  const URL_CHECKS = ['Domain legitimacy','Typosquatting','SSL status','Page content','Redirect chains','Phishing patterns','Known malicious patterns']
  return (
    <div className="input-panel">
      <div className="panel-title">🔗 URL &amp; Link Analysis</div>
      <div className="panel-desc">
        Enter any suspicious URL or link. XGBoost classifies URLs using features such as
        URL length, domain structure, suspicious characters, and other URL threat indicators.
      </div>
      <label className="field-label">URL / Link</label>
      <div className="url-wrapper">
        <span style={{ color:'var(--text-muted)', fontSize:'0.85rem' }}>🔗</span>
        <input
          type="text" className="url-input"
          value={url} onChange={e => setUrl(e.target.value)}
          placeholder="https://suspicious-site.com/verify?token=abc123..."
        />
      </div>
      <div style={{ padding:'1rem', borderRadius:'var(--radius-sm)', background:'rgba(6,182,212,0.06)', border:'1px solid rgba(6,182,212,0.15)', margin:'1.25rem 0' }}>
        <p style={{ fontSize:'0.82rem', color:'var(--text-muted)', marginBottom:6, fontWeight:600 }}>💡 What we check:</p>
        <div className="info-tags">
          {URL_CHECKS.map(c => <span key={c} className="info-tag">{c}</span>)}
        </div>
      </div>
      <button className="analyze-btn" disabled={loading} onClick={() => onSubmit('url', url)}>
        {loading ? '⏳ Analyzing…' : '🔗 Run XGBoost URL Analysis'}
      </button>
    </div>
  )
}

/* ─── Image Panel ── */
function ImagePanel({ loading, onSubmit }) {
  const [file, setFile] = useState(null)
  const DETECTS = [
    ['📄','Document Fraud','Fake IDs, certificates, court orders'],
    ['📸','Screenshot Analysis','Fake conversations, receipts'],
    ['🎨','Synthetic / Forged Media','Deepfakes, manipulated graphics'],
    ['🏷️','Brand Impersonation','Misused logos, fake seals'],
  ]
  return (
    <div className="input-panel">
      <div className="panel-title">🖼️ Image &amp; Screenshot Analysis</div>
      <div className="panel-desc">
        Upload screenshots of messages, government documents, notices, fake receipts,
        or any suspicious image. Vision Transformer (ViT) analyses visual impersonation patterns while OCR extracts text for analysis.
      </div>
      <FileDropZone onFile={setFile} label="Image"/>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(170px,1fr))', gap:10, margin:'1.5rem 0' }}>
        {DETECTS.map(([ic, t, d]) => (
          <div key={t} style={{ padding:12, borderRadius:'var(--radius-sm)', background:'rgba(255,255,255,0.03)', border:'1px solid var(--border-subtle)' }}>
            <div style={{ fontSize:'1.2rem', marginBottom:4 }}>{ic}</div>
            <div style={{ fontSize:'0.82rem', fontWeight:600, marginBottom:2 }}>{t}</div>
            <div style={{ fontSize:'0.75rem', color:'var(--text-muted)' }}>{d}</div>
          </div>
        ))}
      </div>
      <button className="analyze-btn" disabled={loading || !file} onClick={() => onSubmit('image', file)}>
        {loading ? '⏳ Analyzing…' : '🖼️ Run ViT & OCR Analysis'}
      </button>
    </div>
  )
}

/* ─── QR Panel ── */
function QrPanel({ loading, onSubmit }) {
  const [file, setFile] = useState(null)
  const QR_TYPES = ['Payment QR Fraud','Phishing Redirect','Malware Download','Fake Gov QR','Crypto Scam','Data Harvesting','Shortened URL Tricks']
  return (
    <div className="input-panel">
      <div className="panel-title">📱 QR Code Analysis</div>
      <div className="panel-desc">
        Upload an image containing a QR code. QR Code Decoding extracts URLs or text
        and routes the content to the appropriate detection module.
      </div>
      <FileDropZone onFile={setFile} label="QR Code Image" green/>
      <div style={{ margin:'1.5rem 0', padding:'1rem', borderRadius:'var(--radius-sm)', background:'rgba(16,185,129,0.06)', border:'1px solid rgba(16,185,129,0.15)' }}>
        <p style={{ fontSize:'0.82rem', fontWeight:600, color:'var(--emerald)', marginBottom:8 }}>🔍 QR Fraud Types Detected:</p>
        <div className="info-tags">
          {QR_TYPES.map(t => <span key={t} className="info-tag green">{t}</span>)}
        </div>
      </div>
      <button className="analyze-btn" disabled={loading || !file} onClick={() => onSubmit('qr', file)}>
        {loading ? '⏳ Analyzing…' : '📱 Decode & Analyze QR Code'}
      </button>
    </div>
  )
}

/* ─── Audio Panel ── */
function AudioPanel({ loading, onSubmit }) {
  const [file, setFile] = useState(null)
  const SCAM_VECTORS = [
    ['🚨', 'Digital Arrest Scams', 'Fake CBI, police, customs, ED warrants & call isolation'],
    ['🏦', 'Bank & KYC Vishing', 'Urgent freeze threats, OTP/PIN credential harvesting'],
    ['📦', 'Courier / Parcel Interception', 'Fake FedEx/DHL illegal narcotics parcel demands'],
    ['🤖', 'AI Voice Clone Extortion', 'Fake family emergency, accident, or kidnapping scripts'],
  ]
  return (
    <div className="input-panel">
      <div className="panel-title">🎙️ Call Recording &amp; Voice Scam Analysis</div>
      <div className="panel-desc">
        Upload call recordings, voicemails, or audio evidence (.mp3, .wav, .m4a, .aac, .ogg, .flac).
        Speech Acoustic &amp; Vishing Pipeline transcribes conversations, detects authority impersonation (digital arrest, police, bank), high-pressure psychological coercion, and illicit payment demands.
      </div>
      <AudioDropZone onFile={setFile} />
      <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(190px,1fr))', gap:10, margin:'1.5rem 0' }}>
        {SCAM_VECTORS.map(([ic, t, d]) => (
          <div key={t} style={{ padding:12, borderRadius:'var(--radius-sm)', background:'rgba(255,255,255,0.03)', border:'1px solid var(--border-subtle)' }}>
            <div style={{ fontSize:'1.2rem', marginBottom:4 }}>{ic}</div>
            <div style={{ fontSize:'0.82rem', fontWeight:600, marginBottom:2 }}>{t}</div>
            <div style={{ fontSize:'0.75rem', color:'var(--text-muted)' }}>{d}</div>
          </div>
        ))}
      </div>
      <button
        className="analyze-btn"
        style={{
          background: 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)',
          boxShadow: '0 4px 18px rgba(236,72,153,0.3)'
        }}
        disabled={loading || !file}
        onClick={() => onSubmit('audio', file)}
      >
        {loading ? '⏳ Analyzing Call Audio & Transcribing…' : '🎙️ Run Speech & Vishing Analysis'}
      </button>
    </div>
  )
}

/* ─── Main Page ── */
export default function AnalyzePage() {
  const [params]    = useSearchParams()
  const [activeType, setActiveType] = useState(params.get('type') || 'text')
  const [loading, setLoading] = useState(false)
  const navigate    = useNavigate()
  const { showToast } = useToast()

  const handleSubmit = useCallback(async (type, data) => {
    if (!data || (typeof data === 'string' && !data.trim())) {
      showToast('Please provide input before analyzing.', 'error'); return
    }
    setLoading(true)
    try {
      let res
      if (type === 'text')  res = await analyzeText(data)
      if (type === 'url')   res = await analyzeUrl(data)
      if (type === 'image') res = await analyzeImage(data)
      if (type === 'qr')    res = await analyzeQr(data)
      if (type === 'audio') res = await analyzeAudio(data)

      if (!res || !res.data) {
        showToast('No response received from detection server.', 'error')
        return
      }

      const analysis = res.data.analysis
      if (analysis?.id) {
        navigate(`/result/${analysis.id}`)
      } else {
        showToast(res.data.error || 'Analysis failed.', 'error')
      }
    } catch (e) {
      console.error('Analysis submission error:', e)
      showToast(e.response?.data?.error || e.message || 'Network error — is the server running?', 'error')
    } finally {
      setLoading(false)
    }
  }, [navigate, showToast])

  return (
    <>
      <LoadingOverlay active={loading}/>
      <div style={{ padding: '2rem 2rem 4rem', maxWidth: 900, margin: '0 auto' }}>

        <div style={{ marginBottom: '2rem' }}>
          <div className="section-label">🔍 Fraud Analysis</div>
          <h1 style={{ fontSize:'2.2rem', fontWeight:800, marginBottom:'0.4rem' }}>Submit Evidence for Analysis</h1>
          <p style={{ color:'var(--text-secondary)' }}>Select the type of input you want to analyze, then provide the evidence below.</p>
        </div>

        {/* Type Selector */}
        <div className="type-selector">
          {TYPES.map(t => (
            <button key={t.key}
              className={`type-btn ${activeType === t.key ? 'active' : ''}`}
              onClick={() => setActiveType(t.key)}>
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        {/* Panels */}
        {activeType === 'text'  && <TextPanel  loading={loading} onSubmit={handleSubmit}/>}
        {activeType === 'url'   && <UrlPanel   loading={loading} onSubmit={handleSubmit}/>}
        {activeType === 'image' && <ImagePanel loading={loading} onSubmit={handleSubmit}/>}
        {activeType === 'qr'    && <QrPanel    loading={loading} onSubmit={handleSubmit}/>}
        {activeType === 'audio' && <AudioPanel loading={loading} onSubmit={handleSubmit}/>}
      </div>
    </>
  )
}

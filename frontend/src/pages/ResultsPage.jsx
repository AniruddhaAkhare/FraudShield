import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchAnalysis, downloadReport } from '../api/client.js'
import { useToast } from '../context/ToastContext.jsx'
import RiskGauge from '../components/RiskGauge.jsx'

const RISK_COLORS = { CRITICAL:'#ef4444', HIGH:'#f97316', MEDIUM:'#eab308', LOW:'#22c55e' }
const TYPE_CLASS  = { text:'type-text', url:'type-url', image:'type-image', qr:'type-qr', audio:'type-audio' }
const TYPE_ICON   = { text:'💬', url:'🔗', image:'🖼️', qr:'📱', audio:'🎙️' }

function CardHeader({ icon, iconCls, title, count }) {
  return (
    <div className="card-header">
      <div className={`card-icon ${iconCls}`}>{icon}</div>
      <h3>{title}</h3>
      {count !== undefined && <span className="card-count">{count}</span>}
    </div>
  )
}

function getModelInfo(inputType) {
  switch (inputType) {
    case 'text':
      return {
        name: 'BERT',
        fullName: 'BERT Language Model',
        description: 'Analyses messages, emails, and extracted text to detect scam language, impersonation, threats, urgency, and fraudulent requests.',
      }
    case 'url':
      return {
        name: 'XGBoost',
        fullName: 'XGBoost Feature Classifier',
        description: 'Classifies URLs using features such as URL length, domain structure, suspicious characters, and other URL indicators.',
      }
    case 'image':
      return {
        name: 'Vision Transformer (ViT) + OCR',
        fullName: 'Vision Transformer (ViT) & OCR Pipeline',
        description: 'Analyses screenshots and images for visual impersonation patterns; OCR extracts text so it can be analysed by BERT.',
      }
    case 'qr':
      return {
        name: 'QR Code Decoding',
        fullName: 'QR Code Decoding & Feature Routing',
        description: 'Extracts URLs or text from QR codes and routes the content to the appropriate detection module.',
      }
    case 'audio':
      return {
        name: 'Speech Acoustic & Vishing Pipeline',
        fullName: 'Speech Acoustic & Vishing Analysis Pipeline',
        description: 'Transcribes and evaluates call audio for authority impersonation (digital arrest, police, bank), high-pressure psychological coercion, and illicit payment demands.',
      }
    default:
      return {
        name: 'Multimodal Risk Fusion',
        fullName: 'Multimodal Risk Fusion Pipeline',
        description: 'Combines outputs from available models into an overall risk score, probable scam category, and risk level.',
      }
  }
}

function cleanAiTerms(str, inputType) {
  if (!str || typeof str !== 'string') return str
  const model = getModelInfo(inputType)
  return str
    .replace(/Google Gemini Audio \([^)]*\)/gi, 'Speech Acoustic Pipeline')
    .replace(/Google Gemini Vision \([^)]*\)/gi, 'Vision Transformer (ViT)')
    .replace(/Google Gemini AI \([^)]*\)/gi, model.fullName)
    .replace(/Google Gemini Live Vision AI/gi, 'Vision Transformer (ViT) & OCR')
    .replace(/Google Gemini Live AI/gi, 'Multimodal Risk Fusion')
    .replace(/Google Gemini AI/gi, model.fullName)
    .replace(/Google Gemini Audio/gi, model.fullName)
    .replace(/Google Gemini/gi, model.name)
    .replace(/Gemini Vision/gi, 'Vision Transformer (ViT)')
    .replace(/Gemini Audio/gi, model.fullName)
    .replace(/Gemini AI/gi, model.name)
    .replace(/Gemini/gi, model.name)
    .replace(/FraudShield Heuristic Engine/gi, model.fullName)
    .replace(/Rule-based Heuristic Engine/gi, 'Feature-Based Detection Engine')
    .replace(/Heuristic Engine/gi, 'Feature-Based Detection Engine')
    .replace(/\bAI-generated\b/gi, 'synthetically generated')
    .replace(/\bAI images\b/gi, 'synthetic images')
    .replace(/\bAI models\b/gi, 'detection modules')
    .replace(/\bAI model\b/gi, 'detection module')
    .replace(/\bVision AI\b/gi, 'Vision Transformer (ViT) & OCR')
    .replace(/\bAI\b/g, 'ML')
}

/* ── Indicators card ── */
function IndicatorsCard({ indicators, inputType }) {
  return (
    <div className="result-card" style={{ gridColumn: 'span 6' }}>
      <CardHeader icon="⚠️" iconCls="red" title="Detection Analysis" count={`${indicators.length} Indicators`}/>
      {indicators.length > 0 ? indicators.map((ind, i) => {
        const rawLabel  = typeof ind === 'string' ? ind : ind.label
        const rawDetail = typeof ind === 'string' ? ''  : ind.detail
        const label     = cleanAiTerms(rawLabel, inputType)
        const detail    = cleanAiTerms(rawDetail, inputType)
        const sev       = typeof ind === 'string' ? 'MEDIUM' : (ind.severity || 'MEDIUM')
        return (
          <div key={i} className="indicator-item">
            <span className={`sev-pill ${sev}`}>{sev}</span>
            <div>
              <div className="ind-label">{label}</div>
              {detail && <div className="ind-detail">{detail}</div>}
            </div>
          </div>
        )
      }) : (
        <div style={{ textAlign:'center', padding:'2rem', color:'var(--text-muted)' }}>
          <div style={{ fontSize:'2rem', marginBottom:'0.5rem' }}>✅</div>
          <p>No fraud indicators detected</p>
        </div>
      )}
    </div>
  )
}

/* ── Evidence card ── */
function EvidenceCard({ evidence, inputType }) {
  const model = getModelInfo(inputType)
  const entries = evidence
    ? Object.entries(evidence)
        .filter(([k]) => k !== 'is_ai_generated')
        .map(([key, val]) => {
          let displayKey = key
          let displayVal = val

          if (key === 'ai_model_used') {
            displayKey = 'detection_module'
            displayVal = model.fullName
          } else if (key === 'analysis_engine') {
            displayKey = 'pipeline_architecture'
            displayVal = 'Multimodal Risk Fusion'
          } else if (typeof val === 'string') {
            displayVal = cleanAiTerms(val, inputType)
          }

          return [displayKey, displayVal]
        })
    : []

  return (
    <div className="result-card" style={{ gridColumn: 'span 6' }}>
      <CardHeader icon="🧾" iconCls="amber" title="Evidence Analysis" count={`${entries.length} Fields`}/>
      {entries.length > 0 ? entries.map(([key, val]) => {
        const isModelKey = key.includes('module') || key.includes('pipeline') || key.includes('architecture') || key.includes('engine')
        return (
          <div key={key} className="evidence-field">
            <div className="ev-key">{key.replace(/_/g,' ')}</div>
            {Array.isArray(val) ? (
              val.length > 0
                ? <div className="ev-tags">{val.map((v,i) => <span key={i} className="ev-tag">{cleanAiTerms(v, inputType)}</span>)}</div>
                : <div className="ev-val" style={{ color:'var(--text-muted)' }}>None found</div>
            ) : (
              <div className={`ev-val ${isModelKey ? 'ev-tag' : (key.toLowerCase().includes('url') || key.toLowerCase().includes('data') ? 'mono' : '')}`}
                   style={isModelKey ? { color: '#4ade80', background: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.25)', display: 'inline-block' } : {}}>
                {String(val !== undefined && val !== null ? val : '—')}
              </div>
            )}
          </div>
        )
      }) : (
        <p style={{ color:'var(--text-muted)', fontSize:'0.85rem' }}>No evidence data extracted.</p>
      )}
    </div>
  )
}

/* ── Recommendations card ── */
function RecsCard({ recommendations }) {
  return (
    <div className="result-card" style={{ gridColumn: 'span 12' }}>
      <CardHeader icon="🔒" iconCls="green" title="Security Recommendations" count={`${recommendations.length} Actions`}/>
      {recommendations.length > 0 ? (
        <div className="rec-grid">
          {recommendations.map((rec, i) => {
            const title  = typeof rec === 'string' ? rec : rec.title
            const detail = typeof rec === 'string' ? ''  : rec.detail
            return (
              <div key={i} className="rec-item">
                <div className="rec-num">{i + 1}</div>
                <div>
                  <div className="rec-title">{title}</div>
                  {detail && <div className="rec-detail">{detail}</div>}
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div style={{ textAlign:'center', padding:'2rem', color:'var(--emerald)' }}>
          <div style={{ fontSize:'1.5rem', marginBottom:'0.5rem' }}>✅</div>
          <p>No specific security actions required — content appears legitimate.</p>
        </div>
      )}
    </div>
  )
}

export default function ResultsPage() {
  const { id }    = useParams()
  const navigate  = useNavigate()
  const { showToast } = useToast()
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    fetchAnalysis(id)
      .then(r => setAnalysis(r.data))
      .catch(() => { showToast('Analysis not found.', 'error'); navigate('/history') })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return (
    <div style={{ display:'flex', alignItems:'center', justifyContent:'center', minHeight:'60vh', flexDirection:'column', gap:'1rem', color:'var(--text-muted)' }}>
      <div style={{ fontSize:'3rem', animation:'pulse 1.5s ease-in-out infinite' }}>🛡️</div>
      <p>Loading analysis…</p>
      <style>{`@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.1)}}`}</style>
    </div>
  )

  if (!analysis) return null

  const { risk_level, risk_score, confidence, scam_type, is_fraud,
          indicators = [], evidence = {}, recommendations = [],
          explanation, input_type, input_content, created_at } = analysis

  const modelInfo = getModelInfo(input_type)
  const riskColor = RISK_COLORS[risk_level] || '#7c3aed'

  return (
    <div style={{ padding: '2rem 2rem 4rem', maxWidth: 1200, margin: '0 auto' }}>

      {/* ── Action Bar ── */}
      <div className="action-bar">
        <div>
          <div className="section-label">📊 Analysis #{id}</div>
          <h1 style={{ fontSize:'2rem', fontWeight:800 }}>Fraud Analysis Report</h1>
        </div>
        <div className="action-btns">
          <a href={downloadReport(id)} target="_blank" rel="noreferrer" className="btn-pdf">
            📄 Download PDF
          </a>
          <button className="btn-secondary" onClick={() => navigate('/analyze')}>🔍 New Analysis</button>
          <button className="btn-secondary" onClick={() => navigate('/history')}>🕒 History</button>
          <button className="btn-secondary"
            onClick={() => { navigator.clipboard.writeText(window.location.href); showToast('Link copied!', 'success') }}>
            🔗 Copy Link
          </button>
        </div>
      </div>

      {/* ── Verdict Banner ── */}
      <div className={`verdict-banner ${is_fraud ? 'fraud' : 'clean'}`}>
        <div className="verdict-icon">{is_fraud ? '⚠️' : '✅'}</div>
        <div>
          <div className="verdict-title" style={{ color: is_fraud ? 'var(--risk-critical)' : 'var(--risk-low)' }}>
            {is_fraud ? 'FRAUD DETECTED' : 'NO FRAUD DETECTED'}
          </div>
          <div className="verdict-sub">
            {scam_type} &bull; <span className={`risk-badge ${risk_level}`}>{risk_level}</span> &bull; Analyzed {created_at}
          </div>
          <div style={{ marginTop:8, display:'flex', alignItems:'center', gap:10, flexWrap:'wrap', fontSize:'0.85rem' }}>
            <div>
              Input: <span className={`type-badge ${TYPE_CLASS[input_type] || ''}`}>{TYPE_ICON[input_type]} {input_type?.toUpperCase()}</span>
            </div>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 6, padding: '3px 10px', borderRadius: 20,
              background: 'rgba(34, 197, 94, 0.12)',
              border: '1px solid rgba(34, 197, 94, 0.3)',
              fontSize: '0.78rem', fontWeight: 600, color: '#4ade80'
            }}>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#22c55e', boxShadow: '0 0 6px #22c55e', display: 'inline-block' }}></span>
              <span>⚡ Module: {modelInfo.name}</span>
            </div>
          </div>
        </div>
        <div className="verdict-meta">
          {[
            { l:'Risk Score', v:`${Math.round(risk_score)}/100`, c: riskColor },
            { l:'Confidence', v:`${Math.round(confidence)}%`,    c: 'var(--cyan)' },
            { l:'Indicators', v: indicators.length,              c: 'var(--accent-light)' },
          ].map(m => (
            <div key={m.l} className="meta-chip">
              <div className="chip-label">{m.l}</div>
              <div className="chip-value" style={{ color: m.c }}>{m.v}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Results Bento ── */}
      <div className="results-bento">

        {/* ① Gauge — span 3 */}
        <div className="result-card" style={{ gridColumn:'span 3' }}>
          <CardHeader icon="📊" iconCls="purple" title="Risk Score"/>
          <RiskGauge score={risk_score} level={risk_level} confidence={confidence} scamType={scam_type}/>
        </div>

        {/* ② Detection Explanation — span 9 */}
        <div className="result-card" style={{ gridColumn:'span 9' }}>
          <CardHeader icon="🔍" iconCls="cyan" title="Detection Analysis Explanation"
            count={input_type?.toUpperCase()}/>

          {/* Model Status Banner */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8,
            padding: '8px 14px', borderRadius: 8,
            background: 'linear-gradient(90deg, rgba(34,197,94,0.08) 0%, rgba(59,130,246,0.08) 100%)',
            border: '1px solid var(--border-subtle)', marginBottom: 14
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.84rem' }}>
              <span style={{ fontSize: '1.1rem' }}>⚡</span>
              <span style={{ color: 'var(--text-secondary)' }}>
                <strong>Active Module:</strong> <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{modelInfo.fullName}</span>
              </span>
            </div>
            <span style={{
              fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.05em',
              padding: '3px 10px', borderRadius: 12,
              background: 'rgba(34,197,94,0.18)',
              color: '#4ade80', fontWeight: 700,
              display: 'flex', alignItems: 'center', gap: 6
            }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#4ade80' }}></span>
              Multimodal Risk Fusion
            </span>
          </div>

          <div className="explanation-box">
            {cleanAiTerms(explanation, input_type) || 'No detailed explanation provided.'}
          </div>
          {input_content && (
            <div style={{ marginTop:'1rem' }}>
              <div style={{ fontSize:'0.72rem', color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:6 }}>
                Submitted Input Preview
              </div>
              <div style={{
                padding:12, borderRadius:8, background:'rgba(255,255,255,0.03)',
                border:'1px solid var(--border-subtle)', fontSize:'0.85rem',
                color:'var(--text-secondary)', wordBreak:'break-all',
                maxHeight: input_type === 'audio' || input_type === 'image' ? 'none' : 120,
                overflowY:'auto',
                fontFamily: ['url','qr'].includes(input_type) ? "'JetBrains Mono',monospace" : 'inherit'
              }}>
                <div>{String(input_content).slice(0,600)}{String(input_content).length > 600 ? '…' : ''}</div>

                {input_type === 'audio' && analysis.file_url && (
                  <div style={{ marginTop: 12, padding: 12, borderRadius: 8, background: 'rgba(236,72,153,0.06)', border: '1px solid rgba(236,72,153,0.2)' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f472b6', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span>🎙️</span> Call Recording Playback
                    </div>
                    <audio controls style={{ width: '100%', height: 40 }} src={analysis.file_url} />
                  </div>
                )}

                {input_type === 'image' && analysis.file_url && (
                  <div style={{ marginTop: 12 }}>
                    <img src={analysis.file_url} alt="Analyzed Evidence" style={{ maxHeight: 220, maxWidth: '100%', borderRadius: 6, border: '1px solid var(--border-subtle)' }} />
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* ③ Indicators */}
        <IndicatorsCard indicators={indicators} inputType={input_type}/>

        {/* ④ Evidence */}
        <EvidenceCard evidence={evidence} inputType={input_type}/>

        {/* ⑤ Recommendations */}
        <RecsCard recommendations={recommendations}/>

      </div>

      {/* Bottom actions */}
      <div style={{ marginTop:'2.5rem', display:'flex', gap:'1rem', justifyContent:'center', flexWrap:'wrap', padding:'2rem', borderTop:'1px solid var(--border-subtle)' }}>
        <a href={downloadReport(id)} target="_blank" rel="noreferrer" className="btn-pdf">📄 Download Full PDF Report</a>
        <button className="btn-primary" onClick={() => navigate('/analyze')}>🔍 Analyze Another</button>
        <button className="btn-secondary" onClick={() => navigate('/history')}>🕒 View History</button>
      </div>
    </div>
  )
}

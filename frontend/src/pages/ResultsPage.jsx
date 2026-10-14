import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchAnalysis, downloadReport } from '../api/client.js'
import { useToast } from '../context/ToastContext.jsx'
import RiskGauge from '../components/RiskGauge.jsx'

const RISK_COLORS = { CRITICAL:'#ef4444', HIGH:'#f97316', MEDIUM:'#eab308', LOW:'#22c55e' }
const TYPE_CLASS  = { text:'type-text', url:'type-url', image:'type-image', qr:'type-qr' }
const TYPE_ICON   = { text:'💬', url:'🔗', image:'🖼️', qr:'📱' }

function CardHeader({ icon, iconCls, title, count }) {
  return (
    <div className="card-header">
      <div className={`card-icon ${iconCls}`}>{icon}</div>
      <h3>{title}</h3>
      {count !== undefined && <span className="card-count">{count}</span>}
    </div>
  )
}

/* ── Indicators card ── */
function IndicatorsCard({ indicators }) {
  return (
    <div className="result-card" style={{ gridColumn: 'span 6' }}>
      <CardHeader icon="⚠️" iconCls="red" title="Detection Analysis" count={`${indicators.length} Indicators`}/>
      {indicators.length > 0 ? indicators.map((ind, i) => {
        const label  = typeof ind === 'string' ? ind : ind.label
        const detail = typeof ind === 'string' ? ''  : ind.detail
        const sev    = typeof ind === 'string' ? 'MEDIUM' : (ind.severity || 'MEDIUM')
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
function EvidenceCard({ evidence }) {
  const entries = evidence ? Object.entries(evidence) : []
  return (
    <div className="result-card" style={{ gridColumn: 'span 6' }}>
      <CardHeader icon="🧾" iconCls="amber" title="Evidence Analysis" count={`${entries.length} Fields`}/>
      {entries.length > 0 ? entries.map(([key, val]) => {
        const isModelKey = key.includes('ai_model') || key.includes('engine')
        return (
          <div key={key} className="evidence-field">
            <div className="ev-key">{key.replace(/_/g,' ')}</div>
            {Array.isArray(val) ? (
              val.length > 0
                ? <div className="ev-tags">{val.map((v,i) => <span key={i} className="ev-tag">{v}</span>)}</div>
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
          explanation, input_type, input_content, created_at,
          ai_model, engine, is_ai_generated } = analysis

  const resolvedModel = ai_model || evidence?.ai_model_used || 'Google Gemini AI'
  const isAi = is_ai_generated !== undefined ? is_ai_generated : (evidence?.is_ai_generated !== false)
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
              background: isAi ? 'rgba(34, 197, 94, 0.12)' : 'rgba(234, 179, 8, 0.12)',
              border: isAi ? '1px solid rgba(34, 197, 94, 0.3)' : '1px solid rgba(234, 179, 8, 0.3)',
              fontSize: '0.78rem', fontWeight: 600, color: isAi ? '#4ade80' : '#facc15'
            }}>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: isAi ? '#22c55e' : '#eab308', boxShadow: isAi ? '0 0 6px #22c55e' : 'none', display: 'inline-block' }}></span>
              <span>{isAi ? `✨ ${resolvedModel}` : `⚙️ Engine: ${resolvedModel}`}</span>
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

        {/* ② AI Explanation — span 9 */}
        <div className="result-card" style={{ gridColumn:'span 9' }}>
          <CardHeader icon="🧠" iconCls="cyan" title="AI Analysis Explanation"
            count={input_type?.toUpperCase()}/>

          {/* AI Engine Status Banner */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8,
            padding: '8px 14px', borderRadius: 8,
            background: isAi ? 'linear-gradient(90deg, rgba(34,197,94,0.08) 0%, rgba(59,130,246,0.08) 100%)' : 'rgba(255,255,255,0.03)',
            border: '1px solid var(--border-subtle)', marginBottom: 14
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.84rem' }}>
              <span style={{ fontSize: '1.1rem' }}>{isAi ? '✨' : '⚙️'}</span>
              <span style={{ color: 'var(--text-secondary)' }}>
                <strong>Engine:</strong> <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{resolvedModel}</span>
              </span>
            </div>
            <span style={{
              fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.05em',
              padding: '3px 10px', borderRadius: 12,
              background: isAi ? 'rgba(34,197,94,0.18)' : 'rgba(234,179,8,0.18)',
              color: isAi ? '#4ade80' : '#facc15', fontWeight: 700,
              display: 'flex', alignItems: 'center', gap: 6
            }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: isAi ? '#4ade80' : '#facc15' }}></span>
              {isAi ? 'Direct Google Gemini AI Output' : 'Heuristic Engine'}
            </span>
          </div>

          <div className="explanation-box">
            {explanation || 'No detailed explanation provided.'}
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
                maxHeight:120, overflowY:'auto',
                fontFamily: ['url','qr'].includes(input_type) ? "'JetBrains Mono',monospace" : 'inherit'
              }}>
                {String(input_content).slice(0,600)}{String(input_content).length > 600 ? '…' : ''}
              </div>
            </div>
          )}
        </div>

        {/* ③ Indicators */}
        <IndicatorsCard indicators={indicators}/>

        {/* ④ Evidence */}
        <EvidenceCard evidence={evidence}/>

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

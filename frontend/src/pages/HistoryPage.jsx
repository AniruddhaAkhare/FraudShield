import { useEffect, useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchHistory, downloadReport } from '../api/client.js'

const TYPE_CLASS = { text:'type-text', url:'type-url', image:'type-image', qr:'type-qr', audio:'type-audio' }
const TYPE_ICON  = { text:'💬 TEXT', url:'🔗 URL', image:'🖼️ IMAGE', qr:'📱 QR', audio:'🎙️ AUDIO' }
const RISK_COLOR = { CRITICAL:'#ef4444', HIGH:'#f97316', MEDIUM:'#eab308', LOW:'#22c55e' }

function ScoreBar({ score, level }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:6 }}>
      <div className="score-bar">
        <div className="score-fill" style={{ width:`${score}%`, background: RISK_COLOR[level] || '#7c3aed' }}/>
      </div>
      <span style={{ fontWeight:700, fontSize:'0.85rem' }}>{Math.round(score)}</span>
    </div>
  )
}

export default function HistoryPage() {
  const navigate = useNavigate()
  const [records, setRecords] = useState([])
  const [stats,   setStats]   = useState({ total:0, fraud:0, clean:0, fraud_rate:0 })
  const [loading, setLoading] = useState(true)
  const [search,  setSearch]  = useState('')
  const [typeFilter,    setTypeFilter]    = useState('all')
  const [verdictFilter, setVerdictFilter] = useState('all')

  useEffect(() => {
    fetchHistory()
      .then(r => { setRecords(r.data.records); setStats(r.data.stats) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => records.filter(r => {
    const q = search.toLowerCase()
    const matchSearch  = !q || JSON.stringify(r).toLowerCase().includes(q)
    const matchType    = typeFilter === 'all'    || r.input_type === typeFilter
    const matchVerdict = verdictFilter === 'all' ||
      (verdictFilter === 'fraud' && r.is_fraud)  ||
      (verdictFilter === 'clean' && !r.is_fraud)
    return matchSearch && matchType && matchVerdict
  }), [records, search, typeFilter, verdictFilter])

  return (
    <div style={{ padding:'2rem 2rem 4rem', maxWidth:1200, margin:'0 auto' }}>

      {/* Header */}
      <div style={{ marginBottom:'2rem' }}>
        <div className="section-label">🕒 Analysis History</div>
        <h1 style={{ fontSize:'2.2rem', fontWeight:800, marginBottom:'0.4rem' }}>Detection History</h1>
        <p style={{ color:'var(--text-secondary)' }}>All previous fraud analysis results. Click any row to view full details.</p>
      </div>

      {/* Stats Bar */}
      <div className="stats-bar">
        <div className="stat-card total">
          <div className="stat-card-label">Total Analyses</div>
          <div className="stat-card-value">{stats.total}</div>
        </div>
        <div className="stat-card fraud">
          <div className="stat-card-label">Frauds Detected</div>
          <div className="stat-card-value">{stats.fraud}</div>
        </div>
        <div className="stat-card clean">
          <div className="stat-card-label">Clean Results</div>
          <div className="stat-card-value">{stats.clean}</div>
        </div>
        <div className="stat-card rate">
          <div className="stat-card-label">Fraud Rate</div>
          <div className="stat-card-value">{stats.fraud_rate}%</div>
        </div>
      </div>

      {/* Type Distribution */}
      {records.length > 0 && (
        <div style={{ display:'flex', gap:12, flexWrap:'wrap', marginBottom:'1.5rem' }}>
          {['text','url','image','qr','audio'].map(t => {
            const count = records.filter(r => r.input_type === t).length
            return (
              <div key={t} style={{ display:'flex', alignItems:'center', gap:8, padding:'8px 16px', borderRadius:'var(--radius-sm)', background:'var(--bg-card)', border:'1px solid var(--border-subtle)' }}>
                <span className={`type-badge ${TYPE_CLASS[t] || ''}`}>{TYPE_ICON[t] || t.toUpperCase()}</span>
                <span style={{ fontWeight:700 }}>{count}</span>
              </div>
            )
          })}
        </div>
      )}

      {/* Table */}
      <div className="history-table-wrap">
        <div className="history-filters">
          <input
            type="text" className="filter-input"
            placeholder="🔍 Search by content, type, or scam…"
            value={search} onChange={e => setSearch(e.target.value)}
          />
          <select className="filter-select" value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
            <option value="all">All Types</option>
            <option value="text">💬 Text</option>
            <option value="url">🔗 URL</option>
            <option value="image">🖼️ Image</option>
            <option value="qr">📱 QR Code</option>
            <option value="audio">🎙️ Call Recording</option>
          </select>
          <select className="filter-select" value={verdictFilter} onChange={e => setVerdictFilter(e.target.value)}>
            <option value="all">All Verdicts</option>
            <option value="fraud">⚠️ Fraud</option>
            <option value="clean">✅ Clean</option>
          </select>
        </div>

        {loading ? (
          <div style={{ textAlign:'center', padding:'4rem', color:'var(--text-muted)' }}>
            <div style={{ fontSize:'2rem', marginBottom:'1rem', animation:'spin 1s linear infinite', display:'inline-block' }}>⏳</div>
            <p>Loading history…</p>
            <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🛡️</div>
            <h3 style={{ marginBottom:'0.5rem', color:'var(--text-secondary)' }}>
              {records.length === 0 ? 'No analyses yet' : 'No results match your filters'}
            </h3>
            <p>
              {records.length === 0
                ? <span>Start by <button className="sample-btn" style={{display:'inline'}} onClick={() => navigate('/analyze')}>analyzing your first evidence</button></span>
                : 'Try adjusting your search or filter criteria.'}
            </p>
          </div>
        ) : (
          <div style={{ overflowX:'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Type</th>
                  <th>Content Preview</th>
                  <th>Module</th>
                  <th>Scam Type</th>
                  <th>Risk Score</th>
                  <th>Level</th>
                  <th>Verdict</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(r => (
                  <tr key={r.id} onClick={() => navigate(`/result/${r.id}`)}>
                    <td style={{ color:'var(--text-muted)', fontSize:'0.8rem' }}>#{r.id}</td>
                    <td>
                      <span className={`type-badge ${TYPE_CLASS[r.input_type] || ''}`}>
                        {TYPE_ICON[r.input_type] || r.input_type?.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ maxWidth:180 }}>
                      <div style={{ overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', fontSize:'0.82rem', color:'var(--text-secondary)' }}
                        title={r.input_content || ''}>
                        {String(r.input_content || '—').slice(0, 65)}{String(r.input_content || '').length > 65 ? '…' : ''}
                      </div>
                    </td>
                    <td>
                      <span style={{
                        fontSize: '0.72rem', fontWeight: 600, padding: '2px 8px', borderRadius: 12,
                        background: 'rgba(34,197,94,0.12)',
                        color: '#4ade80',
                        border: '1px solid rgba(34,197,94,0.25)',
                        whiteSpace: 'nowrap', display: 'inline-block'
                      }}>
                        {r.input_type === 'text' ? 'BERT' :
                         r.input_type === 'url' ? 'XGBoost' :
                         r.input_type === 'image' ? 'Vision Transformer (ViT)' : 'QR Decoding'}
                      </span>
                    </td>
                    <td style={{ fontSize:'0.85rem' }}>{r.scam_type}</td>
                    <td><ScoreBar score={r.risk_score} level={r.risk_level}/></td>
                    <td><span className={`risk-badge ${r.risk_level}`} style={{ fontSize:'0.72rem', padding:'3px 10px' }}>{r.risk_level}</span></td>
                    <td>
                      <span className={`verdict-pill ${r.is_fraud ? 'fraud' : 'clean'}`}>
                        {r.is_fraud ? '⚠️ Fraud' : '✅ Clean'}
                      </span>
                    </td>
                    <td style={{ fontSize:'0.8rem', color:'var(--text-muted)', whiteSpace:'nowrap' }}>
                      {r.created_at ? r.created_at.slice(0,16) : '—'}
                    </td>
                    <td onClick={e => e.stopPropagation()}>
                      <div style={{ display:'flex', gap:6 }}>
                        <button className="tbl-action-btn tbl-view" onClick={() => navigate(`/result/${r.id}`)}>View</button>
                        <a href={downloadReport(r.id)} target="_blank" rel="noreferrer"
                          className="tbl-action-btn tbl-pdf">PDF</a>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

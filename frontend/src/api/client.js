import axios from 'axios'

const api = axios.create({ baseURL: '' })

export const analyzeText  = (message)    => api.post('/api/analyze/text',  { message })
export const analyzeUrl   = (url)        => api.post('/api/analyze/url',   { url })

export const analyzeImage = (file) => {
  const fd = new FormData(); fd.append('file', file)
  return api.post('/api/analyze/image', fd)
}
export const analyzeQr = (file) => {
  const fd = new FormData(); fd.append('file', file)
  return api.post('/api/analyze/qr', fd)
}
export const analyzeAudio = (file) => {
  const fd = new FormData(); fd.append('file', file)
  return api.post('/api/analyze/audio', fd)
}

export const fetchHistory    = ()   => api.get('/api/history')
export const fetchAnalysis   = (id) => api.get(`/api/analysis/${id}`)
export const fetchStats      = ()   => api.get('/api/stats')
export const downloadReport  = (id) => `/api/report/${id}`

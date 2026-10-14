import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'

export default function FileDropZone({ onFile, accept = 'image/*', green = false, label = 'Image' }) {
  const [preview, setPreview] = useState(null)
  const [fileInfo, setFileInfo] = useState(null)

  const onDrop = useCallback(files => {
    const f = files[0]
    if (!f) return
    setFileInfo({ name: f.name, size: (f.size / 1024).toFixed(1) + ' KB' })
    if (f.type.startsWith('image/')) {
      const reader = new FileReader()
      reader.onload = e => setPreview(e.target.result)
      reader.readAsDataURL(f)
    }
    onFile(f)
  }, [onFile])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'image/*': [] }, multiple: false,
  })

  return (
    <div>
      <div {...getRootProps()} className={`drop-zone ${isDragActive ? 'dragover' : ''}`}>
        <input {...getInputProps()} />
        <div className="drop-icon">{green ? '📱' : '🖼️'}</div>
        <div className="drop-title">Drag & Drop {label} Here</div>
        <div style={{ margin: '8px 0', color: 'var(--text-muted)', fontSize: '0.82rem' }}>— or —</div>
        <button type="button" className={`browse-btn ${green ? 'green' : ''}`}
          onClick={e => { e.stopPropagation() }}>
          Browse File
        </button>
        <div className="drop-hint" style={{ marginTop: '0.75rem' }}>
          Supports: JPG, PNG, GIF, BMP, WebP (max 16MB)
        </div>
      </div>

      {fileInfo && (
        <div className="file-preview-box">
          {preview && <img src={preview} alt="preview"/>}
          <div>
            <div className="file-preview-name">{fileInfo.name}</div>
            <div className="file-preview-size">{fileInfo.size}</div>
          </div>
          <span style={{ color: 'var(--emerald)', fontSize: '0.85rem', fontWeight: 600, marginLeft: 'auto' }}>
            ✓ Ready
          </span>
        </div>
      )}
    </div>
  )
}

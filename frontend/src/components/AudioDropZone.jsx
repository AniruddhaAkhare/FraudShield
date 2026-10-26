import { useCallback, useState, useRef, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'

export default function AudioDropZone({ onFile }) {
  const [audioUrl, setAudioUrl] = useState(null)
  const [fileInfo, setFileInfo] = useState(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const audioRef = useRef(null)

  const handleFile = useCallback((f) => {
    if (!f) return
    const url = URL.createObjectURL(f)
    setAudioUrl(url)
    setFileInfo({
      name: f.name,
      size: (f.size / (1024 * 1024)).toFixed(2) + ' MB',
      type: f.type || 'audio/recording'
    })
    setIsPlaying(false)
    setCurrentTime(0)
    onFile(f)
  }, [onFile])

  const onDrop = useCallback((files) => {
    const f = files[0]
    handleFile(f)
  }, [handleFile])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a', '.ogg', '.aac', '.flac', '.webm', '.opus', '.wma']
    },
    multiple: false,
  })

  const togglePlay = () => {
    if (!audioRef.current) return
    if (isPlaying) {
      audioRef.current.pause()
      setIsPlaying(false)
    } else {
      audioRef.current.play()
      setIsPlaying(true)
    }
  }

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime)
    }
  }

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration)
    }
  }

  const handleEnded = () => {
    setIsPlaying(false)
    setCurrentTime(0)
  }

  const formatTime = (secs) => {
    if (isNaN(secs)) return '0:00'
    const m = Math.floor(secs / 60)
    const s = Math.floor(secs % 60)
    return `${m}:${s < 10 ? '0' : ''}${s}`
  }

  const removeFile = (e) => {
    e.stopPropagation()
    if (audioUrl) URL.revokeObjectURL(audioUrl)
    setAudioUrl(null)
    setFileInfo(null)
    setIsPlaying(false)
    onFile(null)
  }

  return (
    <div>
      {!fileInfo ? (
        <div {...getRootProps()} className={`drop-zone audio-zone ${isDragActive ? 'dragover' : ''}`}>
          <input {...getInputProps()} />
          <div className="drop-icon" style={{ fontSize: '3rem', filter: 'drop-shadow(0 0 12px rgba(236,72,153,0.35))' }}>🎙️</div>
          <div className="drop-title" style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: 8 }}>
            Drag &amp; Drop Call Recording Here
          </div>
          <div style={{ margin: '8px 0', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            — or click to select from your device —
          </div>
          <button
            type="button"
            className="browse-btn"
            style={{
              background: 'linear-gradient(135deg, rgba(236,72,153,0.2) 0%, rgba(124,58,237,0.2) 100%)',
              borderColor: 'rgba(236,72,153,0.4)',
              color: '#f472b6'
            }}
            onClick={e => e.stopPropagation()}
          >
            Select Audio File
          </button>
          <div className="drop-hint" style={{ marginTop: '0.85rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
            Supports: MP3, WAV, M4A, OGG, AAC, FLAC, WEBM (up to 32MB)
          </div>
        </div>
      ) : (
        <div className="audio-player-card">
          <audio
            ref={audioRef}
            src={audioUrl}
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onEnded={handleEnded}
          />
          <div className="audio-player-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div className="audio-mic-badge">🎙️</div>
              <div>
                <div className="audio-file-title" title={fileInfo.name}>{fileInfo.name}</div>
                <div className="audio-file-meta">{fileInfo.size} &bull; {fileInfo.type}</div>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span className="audio-ready-badge">✓ Ready to Analyze</span>
              <button
                type="button"
                className="audio-change-btn"
                onClick={removeFile}
                title="Remove and select another file"
              >
                ✕ Change
              </button>
            </div>
          </div>

          {/* Interactive Player Controls */}
          <div className="audio-player-controls">
            <button
              type="button"
              className={`audio-play-button ${isPlaying ? 'playing' : ''}`}
              onClick={togglePlay}
            >
              {isPlaying ? '⏸' : '▶'}
            </button>

            {/* Waveform Animation Bars */}
            <div className="audio-waveform-bars">
              {[40, 75, 55, 90, 60, 85, 45, 95, 70, 50, 80, 65, 90, 45, 70, 85, 60, 75].map((h, idx) => (
                <div
                  key={idx}
                  className={`wave-bar ${isPlaying ? 'animating' : ''}`}
                  style={{
                    height: isPlaying ? `${Math.max(15, (h * Math.sin((idx + 1) * 0.7 + currentTime * 3) + 100) / 2)}%` : `${h * 0.35}%`,
                    animationDelay: `${idx * 0.08}s`
                  }}
                />
              ))}
            </div>

            <div className="audio-time-display">
              {formatTime(currentTime)} / {formatTime(duration)}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

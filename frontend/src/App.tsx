import { useState, useEffect } from 'react'
import './App.css'
import { AudioUpload } from './components/AudioUpload'

interface HealthStatus {
  status: string
  models: {
    asr: string
    diarization: string
    vad: string
    enhancement: string
  }
}

function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((data) => {
        setHealth(data)
        setLoading(false)
      })
      .catch((err) => {
        console.error('Failed to fetch health:', err)
        setLoading(false)
      })
  }, [])

  return (
    <div className="app">
      <header className="header">
        <h1>VoxTrace</h1>
        <p className="subtitle">Low-quality Audio Robust Speech Recognition</p>
      </header>

      <main className="main">
        {/* Audio Upload Component */}
        <AudioUpload onUploadComplete={(result) => {
          console.log('Upload complete:', result)
        }} />

        <section className="status-section">
          <h2>System Status</h2>
          {loading ? (
            <p>Loading...</p>
          ) : health ? (
            <div className="status-grid">
              <div className="status-item">
                <span className="status-label">API Status:</span>
                <span className={`status-value ${health.status}`}>
                  {health.status}
                </span>
              </div>
              <div className="status-item">
                <span className="status-label">ASR Model:</span>
                <span className="status-value">{health.models.asr}</span>
              </div>
              <div className="status-item">
                <span className="status-label">Diarization:</span>
                <span className="status-value">{health.models.diarization}</span>
              </div>
              <div className="status-item">
                <span className="status-label">VAD:</span>
                <span className="status-value">{health.models.vad}</span>
              </div>
              <div className="status-item">
                <span className="status-label">Enhancement:</span>
                <span className="status-value">{health.models.enhancement}</span>
              </div>
            </div>
          ) : (
            <p className="error">Failed to connect to backend</p>
          )}
        </section>

        <section className="info-section">
          <h2>🚀 Phase 2: Audio Pipeline (In Progress)</h2>
          <ul>
            <li>✅ Database initialization</li>
            <li>✅ File upload with metadata extraction</li>
            <li>✅ Frontend upload UI with drag & drop</li>
            <li>⏳ VAD (Voice Activity Detection)</li>
            <li>⏳ Audio enhancement preprocessing</li>
          </ul>
          <p className="phase-note">
            Phase 2 진행 중: 실제 오디오 파일 처리 기능을 구현하고 있습니다.
            위에서 오디오 파일을 업로드하여 테스트해보세요!
          </p>
        </section>
      </main>
    </div>
  )
}

export default App

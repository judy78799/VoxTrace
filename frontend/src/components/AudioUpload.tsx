/**
 * Audio Upload Component
 * Drag & drop or file picker for audio uploads + transcription
 */

import { useState } from 'react'
import { api } from '../services/api'
import type { AudioUploadResponse, TranscriptionResult } from '../types'

interface AudioUploadProps {
  onUploadComplete?: (result: AudioUploadResponse) => void
  onTranscriptionComplete?: (result: TranscriptionResult) => void
}

export function AudioUpload({ onUploadComplete, onTranscriptionComplete }: AudioUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<AudioUploadResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  // Transcription state
  const [transcribing, setTranscribing] = useState(false)
  const [transcription, setTranscription] = useState<TranscriptionResult | null>(null)
  const [transcriptionProgress, setTranscriptionProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState<string>('')
  const [currentStepMessage, setCurrentStepMessage] = useState<string>('')

  // Options
  const [enableEnhancement, setEnableEnhancement] = useState(false)
  const [enableVad, setEnableVad] = useState(true)
  const [enableAutoFilter, setEnableAutoFilter] = useState(false)

  // Filtering UI state
  const [showFilteredSegments, setShowFilteredSegments] = useState(false)

  const handleTranscribe = async () => {
    if (!result?.file_id) return

    setTranscribing(true)
    setTranscriptionProgress(0)
    setCurrentStep('')
    setCurrentStepMessage('')
    setError(null)

    try {
      // Connect to SSE endpoint for real-time progress
      const eventSource = new EventSource(
        `/api/audio/transcribe/stream?` + new URLSearchParams({
          file_id: result.file_id,
          language: 'ko',
          enable_vad: String(enableVad),
          enable_diarization: 'false',
          enable_enhancement: String(enableEnhancement),
          enable_auto_filter: String(enableAutoFilter),
        })
      )

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          // Update progress UI
          setCurrentStep(data.step || '')
          setCurrentStepMessage(data.message || '')
          setTranscriptionProgress(data.progress || 0)

          // Final result received
          if (data.step === 'complete' && data.result) {
            setTranscription(data.result)
            if (onTranscriptionComplete) {
              onTranscriptionComplete(data.result)
            }
            eventSource.close()
            setTranscribing(false)
          }
        } catch (err) {
          console.error('Failed to parse SSE message:', err)
        }
      }

      eventSource.onerror = (err) => {
        console.error('SSE error:', err)
        setError('전사 중 오류가 발생했습니다')
        eventSource.close()
        setTranscribing(false)
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : '전사 실패')
      setTranscribing(false)
    }
  }

  const handleFileSelect = (selectedFile: File | null) => {
    if (!selectedFile) return

    // Validate file type
    if (!selectedFile.type.startsWith('audio/')) {
      setError('오디오 파일만 업로드 가능합니다')
      return
    }

    // Validate file size (500MB max)
    const maxSize = 500 * 1024 * 1024
    if (selectedFile.size > maxSize) {
      setError(`파일이 너무 큽니다 (최대: 500MB, 현재: ${(selectedFile.size / 1024 / 1024).toFixed(1)}MB)`)
      return
    }

    setFile(selectedFile)
    setError(null)
    setResult(null)
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setProgress(0)
    setError(null)

    try {
      // Simulate progress (실제 진행률은 XHR 사용해야 함)
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90))
      }, 200)

      const response = await api.uploadAudio(file)

      clearInterval(progressInterval)
      setProgress(100)
      setResult(response)

      if (onUploadComplete) {
        onUploadComplete(response)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '업로드 실패')
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      handleFileSelect(droppedFile)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  return (
    <div className="audio-upload">
      <h2>🎤 오디오 파일 업로드</h2>

      {/* Dropzone */}
      <div
        className={`dropzone ${isDragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        {file ? (
          <div className="file-info">
            <div className="file-icon">🎵</div>
            <div className="file-details">
              <div className="file-name">{file.name}</div>
              <div className="file-size">{formatFileSize(file.size)}</div>
            </div>
          </div>
        ) : (
          <div className="dropzone-message">
            <div className="dropzone-icon">📁</div>
            <p>오디오 파일을 드래그하거나 클릭하여 선택하세요</p>
            <p className="dropzone-hint">WAV, MP3, M4A, FLAC 등 지원</p>
          </div>
        )}
      </div>

      {/* Hidden file input */}
      <input
        id="file-input"
        type="file"
        accept="audio/*"
        onChange={(e) => handleFileSelect(e.target.files?.[0] || null)}
        style={{ display: 'none' }}
      />

      {/* Upload button */}
      {file && !result && (
        <button
          className="upload-btn"
          onClick={handleUpload}
          disabled={uploading}
        >
          {uploading ? `업로드 중... ${progress}%` : '업로드 시작'}
        </button>
      )}

      {/* Progress bar */}
      {uploading && (
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      {/* Success result */}
      {result && (
        <div className="upload-result">
          <div className="result-header">✅ 업로드 완료!</div>
          <div className="result-details">
            <div className="result-row">
              <span className="result-label">파일 ID:</span>
              <span className="result-value">{result.file_id}</span>
            </div>
            <div className="result-row">
              <span className="result-label">파일명:</span>
              <span className="result-value">{result.filename}</span>
            </div>
            <div className="result-row">
              <span className="result-label">길이:</span>
              <span className="result-value">{formatDuration(result.duration ?? 0)}</span>
            </div>
            <div className="result-row">
              <span className="result-label">샘플레이트:</span>
              <span className="result-value">{result.sample_rate} Hz</span>
            </div>
            <div className="result-row">
              <span className="result-label">채널:</span>
              <span className="result-value">{result.channels === 1 ? 'Mono' : 'Stereo'}</span>
            </div>
            <div className="result-row">
              <span className="result-label">크기:</span>
              <span className="result-value">{formatFileSize(result.size_bytes)}</span>
            </div>
          </div>

          {/* Transcription Options */}
          <div className="transcription-options" style={{ margin: '1rem 0', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={enableEnhancement}
                onChange={(e) => setEnableEnhancement(e.target.checked)}
              />
              <span>🎵 Noise Reduction - 배경 소음 제거 (복도 녹음에 효과적)</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={enableVad}
                onChange={(e) => setEnableVad(e.target.checked)}
              />
              <span>🎙️ VAD (Voice Activity Detection) - 무음 구간 제거</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={enableAutoFilter}
                onChange={(e) => setEnableAutoFilter(e.target.checked)}
              />
              <span>🔍 자동 필터링 - 의심 세그먼트 자동 숨기기 (반복 패턴 등)</span>
            </label>
          </div>

          <button
            className="transcribe-btn"
            onClick={handleTranscribe}
            disabled={transcribing}
          >
            {transcribing ? '전사 중...' : '🎤 음성 인식 시작'}
          </button>

          <button
            className="upload-btn secondary"
            onClick={() => {
              setFile(null)
              setResult(null)
              setProgress(0)
              setTranscription(null)
            }}
          >
            새 파일 업로드
          </button>
        </div>
      )}

      {/* Transcription progress */}
      {transcribing && (
        <div className="transcription-progress">
          <div className="progress-spinner"></div>

          {/* Current Step Message */}
          <p style={{
            fontSize: '1.1rem',
            fontWeight: '600',
            marginTop: '1rem',
            marginBottom: '0.5rem'
          }}>
            {currentStepMessage || '준비 중...'}
          </p>

          {/* Progress bar with percentage */}
          <div className="progress-bar" style={{ marginTop: '1rem' }}>
            <div
              className="progress-fill"
              style={{ width: `${Math.min(transcriptionProgress, 100)}%` }}
            ></div>
          </div>
          <p style={{
            marginTop: '0.5rem',
            fontSize: '1.2rem',
            fontWeight: 'bold',
            color: '#3b82f6'
          }}>
            {Math.floor(transcriptionProgress)}%
          </p>

          {/* Pipeline Steps */}
          <div style={{
            marginTop: '1.5rem',
            padding: '1rem',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            textAlign: 'left'
          }}>
            <div style={{ fontSize: '0.95rem', color: '#666', marginBottom: '0.75rem', fontWeight: '600' }}>
              처리 단계:
            </div>
            {[
              { step: 'loading', label: '오디오 파일 로딩', emoji: '📂' },
              { step: 'analyzing', label: '신호 분석', emoji: '🔬' },
              { step: 'enhancing', label: '배경음 제거 (DeepFilterNet)', emoji: '🎵' },
              { step: 'vad', label: 'VAD 처리 (무음 제거)', emoji: '🎙️' },
              { step: 'transcribing', label: '음성 인식', emoji: '🎤' },
              { step: 'saving', label: '데이터베이스 저장', emoji: '💾' },
              { step: 'post_processing', label: '후처리', emoji: '🔍' },
              { step: 'complete', label: '완료', emoji: '✅' },
            ].map((item, idx) => {
              const isCompleted = transcriptionProgress > idx * (100 / 8)
              const isCurrent = currentStep.includes(item.step)

              return (
                <div
                  key={item.step}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.4rem 0.5rem',
                    marginBottom: '0.3rem',
                    borderRadius: '6px',
                    backgroundColor: isCurrent ? '#e3f2fd' : 'transparent',
                    color: isCompleted ? '#333' : '#999',
                    fontWeight: isCurrent ? '600' : '400',
                    transition: 'all 0.3s ease'
                  }}
                >
                  <span style={{ fontSize: '1.2rem' }}>
                    {isCompleted ? '✓' : item.emoji}
                  </span>
                  <span style={{ flex: 1 }}>{item.label}</span>
                  {isCurrent && (
                    <span style={{ fontSize: '0.8rem', color: '#1976d2' }}>
                      진행 중...
                    </span>
                  )}
                </div>
              )
            })}
          </div>

          <p className="progress-hint" style={{ marginTop: '1rem' }}>
            첫 실행 시 모델 다운로드로 인해 시간이 걸릴 수 있습니다.
          </p>
        </div>
      )}

      {/* Transcription result */}
      {transcription && (
        <div className="transcription-result">
          <div className="result-header">🎯 전사 완료!</div>

          {/* Analysis Section */}
          <div className="analysis-section">
            <h3>📊 분석 정보</h3>

            {/* Performance Metrics */}
            <div className="analysis-grid">
              <div className="analysis-card">
                <div className="card-header">⚡ 성능 지표</div>
                <div className="card-content">
                  <div className="metric-row">
                    <span className="metric-label">처리 시간:</span>
                    <span className="metric-value">{transcription.processing_time.toFixed(2)}초</span>
                  </div>
                  {transcription.rtf && (
                    <div className="metric-row">
                      <span className="metric-label">RTF (Real-Time Factor):</span>
                      <span className="metric-value">{transcription.rtf.toFixed(2)}x</span>
                    </div>
                  )}
                  <div className="metric-row">
                    <span className="metric-label">모델:</span>
                    <span className="metric-value">{transcription.model_version}</span>
                  </div>
                  <div className="metric-row">
                    <span className="metric-label">언어:</span>
                    <span className="metric-value">{transcription.language === 'ko' ? '한국어' : transcription.language}</span>
                  </div>
                </div>
              </div>

              {/* VAD Analysis */}
              {transcription.vad_analysis && (
                <div className="analysis-card">
                  <div className="card-header">🎙️ VAD 분석</div>
                  <div className="card-content">
                    <div className="metric-row">
                      <span className="metric-label">VAD 활성화:</span>
                      <span className="metric-value">{transcription.vad_analysis.enabled ? '✅ 예' : '❌ 아니오'}</span>
                    </div>
                    {transcription.vad_analysis.enabled && transcription.vad_analysis.original_duration && (
                      <>
                        <div className="metric-row">
                          <span className="metric-label">원본 길이:</span>
                          <span className="metric-value">{transcription.vad_analysis.original_duration.toFixed(2)}초</span>
                        </div>
                        <div className="metric-row">
                          <span className="metric-label">처리 후 길이:</span>
                          <span className="metric-value">{transcription.vad_analysis.processed_duration?.toFixed(2)}초</span>
                        </div>
                        <div className="metric-row">
                          <span className="metric-label">제거된 무음:</span>
                          <span className="metric-value highlight">
                            {transcription.vad_analysis.silence_removed?.toFixed(2)}초
                            {transcription.vad_analysis.silence_removed && transcription.vad_analysis.original_duration && (
                              <> ({((transcription.vad_analysis.silence_removed / transcription.vad_analysis.original_duration) * 100).toFixed(1)}%)</>
                            )}
                          </span>
                        </div>
                        <div className="metric-row">
                          <span className="metric-label">음성 세그먼트:</span>
                          <span className="metric-value">{transcription.vad_analysis.speech_segments_count}개</span>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}

              {/* Audio Quality */}
              {transcription.audio_quality && (
                <div className="analysis-card">
                  <div className="card-header">🎵 오디오 품질</div>
                  <div className="card-content">
                    <div className="metric-row">
                      <span className="metric-label">샘플레이트:</span>
                      <span className="metric-value">{transcription.audio_quality.sample_rate} Hz</span>
                    </div>
                    <div className="metric-row">
                      <span className="metric-label">채널:</span>
                      <span className="metric-value">{transcription.audio_quality.channels === 1 ? 'Mono' : 'Stereo'}</span>
                    </div>
                    <div className="metric-row">
                      <span className="metric-label">길이:</span>
                      <span className="metric-value">{formatDuration(transcription.audio_quality.duration)}</span>
                    </div>
                    <div className="metric-row">
                      <span className="metric-label">파일 크기:</span>
                      <span className="metric-value">{transcription.audio_quality.file_size_mb.toFixed(2)} MB</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Signal Analysis */}
              {transcription.signal_analysis && (
                <div className="analysis-card">
                  <div className="card-header">🔬 신호 분석</div>
                  <div className="card-content">
                    <div className="metric-row">
                      <span className="metric-label">품질 점수:</span>
                      <span className={`metric-value ${transcription.signal_analysis.quality_score >= 70 ? 'highlight' : ''}`}>
                        {transcription.signal_analysis.quality_score.toFixed(1)}/100
                      </span>
                    </div>
                    {transcription.signal_analysis.snr_db !== null && transcription.signal_analysis.snr_db !== undefined && (
                      <div className="metric-row">
                        <span className="metric-label">SNR (신호 대 노이즈):</span>
                        <span className="metric-value">{transcription.signal_analysis.snr_db.toFixed(1)} dB</span>
                      </div>
                    )}
                    {transcription.signal_analysis.clipping_detected && (
                      <div className="metric-row">
                        <span className="metric-label">⚠️ 클리핑:</span>
                        <span className="metric-value">{transcription.signal_analysis.clipping_percentage.toFixed(2)}%</span>
                      </div>
                    )}
                    {transcription.signal_analysis.quality_issues.length > 0 && (
                      <>
                        <div className="metric-row">
                          <span className="metric-label">품질 문제:</span>
                          <span className="metric-value">{transcription.signal_analysis.quality_issues.length}개</span>
                        </div>
                        <div className="quality-issues-list">
                          {transcription.signal_analysis.quality_issues.map((issue, idx) => (
                            <div key={idx} className="quality-issue">⚠️ {issue}</div>
                          ))}
                        </div>
                      </>
                    )}

                    {/* Frequency Analysis */}
                    {transcription.signal_analysis.frequency_analysis && (
                      <div className="frequency-analysis" style={{ marginTop: '1rem' }}>
                        <div className="metric-label" style={{ marginBottom: '0.5rem' }}>🎵 주파수 분석</div>
                        <div className="metric-row">
                          <span className="metric-label">저주파 (0-300Hz):</span>
                          <span className="metric-value">{(transcription.signal_analysis.frequency_analysis.low_freq_energy * 100).toFixed(1)}%</span>
                        </div>
                        <div className="metric-row">
                          <span className="metric-label">중간주파 (300-3000Hz):</span>
                          <span className="metric-value">{(transcription.signal_analysis.frequency_analysis.mid_freq_energy * 100).toFixed(1)}%</span>
                        </div>
                        <div className="metric-row">
                          <span className="metric-label">고주파 (3000Hz+):</span>
                          <span className="metric-value">{(transcription.signal_analysis.frequency_analysis.high_freq_energy * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Confidence Statistics */}
              <div className="analysis-card">
                <div className="card-header">📈 신뢰도 통계</div>
                <div className="card-content">
                  {(() => {
                    const confidences = transcription.segments
                      .map(s => s.confidence)
                      .filter((c): c is number => c !== null && c !== undefined)

                    if (confidences.length === 0) {
                      return <div className="metric-row">데이터 없음</div>
                    }

                    const avg = confidences.reduce((a, b) => a + b, 0) / confidences.length
                    const min = Math.min(...confidences)
                    const max = Math.max(...confidences)

                    return (
                      <>
                        <div className="metric-row">
                          <span className="metric-label">평균 신뢰도:</span>
                          <span className="metric-value">{(avg * 100).toFixed(1)}%</span>
                        </div>
                        <div className="metric-row">
                          <span className="metric-label">최소 신뢰도:</span>
                          <span className="metric-value">{(min * 100).toFixed(1)}%</span>
                        </div>
                        <div className="metric-row">
                          <span className="metric-label">최대 신뢰도:</span>
                          <span className="metric-value">{(max * 100).toFixed(1)}%</span>
                        </div>
                        <div className="metric-row">
                          <span className="metric-label">세그먼트 수:</span>
                          <span className="metric-value">{transcription.segments.length}개</span>
                        </div>
                      </>
                    )
                  })()}
                </div>
              </div>
            </div>

            {/* Spectrogram Visualization - Full Width */}
            {transcription.signal_analysis?.spectrogram_base64 && (
              <div style={{ marginTop: '2rem' }}>
                <h3 style={{ marginBottom: '1rem' }}>📊 스펙트로그램 (Mel Spectrogram)</h3>
                <div style={{
                  width: '100%',
                  backgroundColor: '#fff',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  border: '1px solid #e0e0e0'
                }}>
                  <img
                    src={`data:image/png;base64,${transcription.signal_analysis.spectrogram_base64}`}
                    alt="Audio Spectrogram"
                    style={{
                      width: '100%',
                      height: 'auto',
                      display: 'block',
                      borderRadius: '8px',
                    }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Transcription Segments */}
          <div className="segments-container">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3>📝 전사 결과</h3>
              {(() => {
                const suspiciousCount = transcription.segments.filter(s => s.is_suspicious).length
                const filteredCount = transcription.segments.filter(s => s.is_filtered).length

                return suspiciousCount > 0 && (
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', fontSize: '0.9rem' }}>
                    <span style={{ color: '#ff9800' }}>
                      ⚠️ 의심 세그먼트: {suspiciousCount}개
                    </span>
                    {filteredCount > 0 && (
                      <label style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={showFilteredSegments}
                          onChange={(e) => setShowFilteredSegments(e.target.checked)}
                        />
                        <span>숨겨진 세그먼트 표시 ({filteredCount}개)</span>
                      </label>
                    )}
                  </div>
                )
              })()}
            </div>

            {transcription.segments
              .filter(segment => !segment.is_filtered || showFilteredSegments)
              .map((segment, idx) => {
                // Determine segment styling based on flags
                const hasErrorFlag = segment.quality_flags?.some(f => f.severity === 'error')
                const hasWarningFlag = segment.quality_flags?.some(f => f.severity === 'warning')

                const segmentClassName = segment.is_filtered
                  ? 'segment segment-filtered'
                  : segment.is_suspicious
                  ? 'segment segment-suspicious'
                  : hasErrorFlag
                  ? 'segment segment-error'
                  : hasWarningFlag
                  ? 'segment segment-warning'
                  : 'segment'

                return (
                  <div key={idx} className={segmentClassName}>
                    <div className="segment-time">
                      {formatDuration(segment.start)} - {formatDuration(segment.end)}
                      {segment.is_suspicious && (
                        <span style={{ marginLeft: '0.5rem', color: '#ff5722', fontWeight: 'bold' }}>
                          ⚠️ 의심
                        </span>
                      )}
                      {segment.is_filtered && (
                        <span style={{ marginLeft: '0.5rem', color: '#999', fontStyle: 'italic' }}>
                          (숨김)
                        </span>
                      )}
                    </div>
                    <div className="segment-text">{segment.text}</div>
                    {segment.confidence !== null && segment.confidence !== undefined && (
                      <div className="segment-confidence">
                        신뢰도: {(segment.confidence * 100).toFixed(1)}%
                      </div>
                    )}
                    {segment.quality_flags && segment.quality_flags.length > 0 && (
                      <div className="quality-flags">
                        {segment.quality_flags.map((flag, flagIdx) => (
                          <div
                            key={flagIdx}
                            className={`quality-flag quality-flag-${flag.severity}`}
                            title={flag.reason}
                          >
                            {flag.severity === 'error' ? '🔴' : '⚠️'} {flag.reason}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
          </div>
        </div>
      )}
    </div>
  )
}

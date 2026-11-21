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

  const handleTranscribe = async () => {
    if (!result?.file_id) return

    setTranscribing(true)
    setError(null)

    try {
      const transcriptionResult = await api.transcribeAudio(result.file_id, {
        language: 'ko',
        enable_diarization: false,
        enable_enhancement: false,
      })

      setTranscription(transcriptionResult)

      if (onTranscriptionComplete) {
        onTranscriptionComplete(transcriptionResult)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '전사 실패')
    } finally {
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
              <span className="result-value">{formatDuration(result.duration)}</span>
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
          <p>음성을 텍스트로 변환 중입니다...</p>
          <p className="progress-hint">첫 실행 시 모델 다운로드로 인해 시간이 걸릴 수 있습니다.</p>
        </div>
      )}

      {/* Transcription result */}
      {transcription && (
        <div className="transcription-result">
          <div className="result-header">🎯 전사 완료!</div>

          <div className="transcription-meta">
            <div className="meta-item">
              <span className="meta-label">언어:</span>
              <span className="meta-value">{transcription.language === 'ko' ? '한국어' : transcription.language}</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">처리 시간:</span>
              <span className="meta-value">{transcription.processing_time.toFixed(2)}초</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">모델:</span>
              <span className="meta-value">{transcription.model_version}</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">세그먼트:</span>
              <span className="meta-value">{transcription.segments.length}개</span>
            </div>
          </div>

          <div className="segments-container">
            <h3>전사 결과</h3>
            {transcription.segments.map((segment, idx) => (
              <div key={idx} className="segment">
                <div className="segment-time">
                  {formatDuration(segment.start)} - {formatDuration(segment.end)}
                </div>
                <div className="segment-text">{segment.text}</div>
                {segment.confidence !== null && segment.confidence !== undefined && (
                  <div className="segment-confidence">
                    신뢰도: {(segment.confidence * 100).toFixed(1)}%
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

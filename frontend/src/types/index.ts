/**
 * TypeScript type definitions for VoxTrace
 * Phase 1: Basic types for API communication
 */

export interface AudioUploadResponse {
  file_id: string
  filename: string
  duration?: number
  sample_rate?: number
  channels?: number
  format: string
  size_bytes: number
  uploaded_at: string
}

export interface QualityFlag {
  type: string  // e.g., 'repetition', 'low_confidence'
  severity: string  // 'warning' or 'error'
  reason: string  // Human-readable explanation
}

export interface TranscriptionSegment {
  start: number
  end: number
  text: string
  speaker?: string
  confidence?: number
  quality_flags?: QualityFlag[]
  is_suspicious?: boolean
  is_filtered?: boolean
}

export interface VADAnalysis {
  enabled: boolean
  original_duration?: number
  processed_duration?: number
  silence_removed?: number
  speech_segments_count?: number
}

export interface AudioQualityMetrics {
  sample_rate: number
  channels: number
  duration: number
  file_size_mb: number
}

export interface FrequencyAnalysis {
  low_freq_energy: number
  mid_freq_energy: number
  high_freq_energy: number
  spectral_centroid: number
  spectral_rolloff: number
  spectral_bandwidth: number
}

export interface SignalAnalysis {
  snr_db?: number
  frequency_analysis?: FrequencyAnalysis
  clipping_detected: boolean
  clipping_percentage: number
  rms_energy: number
  zero_crossing_rate: number
  spectrogram_base64?: string
  quality_score: number
  quality_issues: string[]
}

export interface TranscriptionResult {
  file_id: string
  segments: TranscriptionSegment[]
  language: string
  processing_time: number
  model_version: string
  created_at: string
  vad_analysis?: VADAnalysis
  audio_quality?: AudioQualityMetrics
  signal_analysis?: SignalAnalysis
  rtf?: number  // Real-Time Factor
}

export interface ProjectResponse {
  id: string
  name: string
  description?: string
  created_at: string
  updated_at: string
  file_count: number
}

export interface HealthStatus {
  status: string
  models: {
    asr: string
    diarization: string
    vad: string
    enhancement: string
  }
}

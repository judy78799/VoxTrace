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

export interface TranscriptionSegment {
  start: number
  end: number
  text: string
  speaker?: string
  confidence?: number
}

export interface TranscriptionResult {
  file_id: string
  segments: TranscriptionSegment[]
  language: string
  processing_time: number
  model_version: string
  created_at: string
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

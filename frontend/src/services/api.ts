/**
 * API Service
 * Centralized API calls to VoxTrace backend
 */

import type {
  AudioUploadResponse,
  TranscriptionResult,
  ProjectResponse,
  HealthStatus,
} from '../types'

const API_BASE = '/api'

export const api = {
  // Health check
  async getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${API_BASE}/health`)
    return res.json()
  },

  // Audio operations
  async uploadAudio(file: File): Promise<AudioUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const res = await fetch(`${API_BASE}/audio/upload`, {
      method: 'POST',
      body: formData,
    })
    return res.json()
  },

  async transcribeAudio(
    fileId: string,
    options: {
      enable_diarization?: boolean
      enable_enhancement?: boolean
      language?: string
    } = {}
  ): Promise<TranscriptionResult> {
    const res = await fetch(`${API_BASE}/audio/transcribe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_id: fileId,
        enable_diarization: options.enable_diarization ?? true,
        enable_enhancement: options.enable_enhancement ?? false,
        language: options.language ?? 'ko',
      }),
    })
    return res.json()
  },

  // Project operations
  async listProjects(): Promise<ProjectResponse[]> {
    const res = await fetch(`${API_BASE}/projects/`)
    return res.json()
  },

  async createProject(name: string, description?: string): Promise<ProjectResponse> {
    const res = await fetch(`${API_BASE}/projects/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description }),
    })
    return res.json()
  },

  async getProject(projectId: string): Promise<ProjectResponse> {
    const res = await fetch(`${API_BASE}/projects/${projectId}`)
    return res.json()
  },
}

# Phase 2: 음성 파이프라인 구축

**시작일:** 2026-11-18
**상태:** 🚀 진행 중

---

## 🎯 목표

Phase 1에서 구축한 아키텍처 위에 **실제 음성 파일 처리 기능**을 구현합니다.

### 핵심 기능
1. ✅ 음성 파일 실제 업로드 및 저장
2. ✅ 오디오 메타데이터 자동 추출
3. ✅ 데이터베이스 초기화 및 연결
4. ✅ VAD (Voice Activity Detection) 통합
5. ✅ 프론트엔드 업로드 UI

---

## 📋 작업 목록

### 1. 데이터베이스 초기화 (우선순위: 최고)

**파일:** `backend/app/db/init_db.py`

```python
async def init_db():
    """데이터베이스 테이블 자동 생성"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

**필요성:**
- Phase 1에서 정의한 11개 테이블을 실제로 생성
- 첫 실행 시 자동으로 `data/db/voxtrace.db` 생성

**테스트:**
```bash
poetry run python -c "
from app.db.init_db import init_db
import asyncio
asyncio.run(init_db())
"
```

---

### 2. 파일 업로드 구현

**현재 상태:** 더미 응답만 반환
**목표:** 실제 파일을 `data/uploads/`에 저장

**변경 파일:** `backend/app/api/audio.py`

#### Before (Phase 1):
```python
@router.post("/upload")
async def upload_audio(file: UploadFile):
    # 더미 응답
    return AudioUploadResponse(
        file_id="dummy-file-001",
        filename=file.filename,
        ...
    )
```

#### After (Phase 2):
```python
@router.post("/upload")
async def upload_audio(file: UploadFile):
    # 1. 고유 ID 생성
    file_id = str(uuid.uuid4())

    # 2. 파일 저장
    file_path = f"data/uploads/{file_id}_{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 3. 메타데이터 추출 (librosa or FFmpeg)
    duration, sample_rate, channels = extract_metadata(file_path)

    # 4. 데이터베이스에 기록
    audio_file = AudioFile(
        id=file_id,
        filename=file.filename,
        original_path=file_path,
        duration=duration,
        sample_rate=sample_rate,
        channels=channels,
        ...
    )
    db.add(audio_file)
    await db.commit()

    return AudioUploadResponse(...)
```

**의존성 추가:**
```toml
librosa = "^0.10.0"      # 오디오 메타데이터 추출
soundfile = "^0.12.0"    # 오디오 파일 읽기
```

---

### 3. 오디오 메타데이터 추출

**파일:** `backend/app/utils/audio.py` (새로 생성)

```python
import librosa
import soundfile as sf

def extract_audio_metadata(file_path: str) -> dict:
    """
    오디오 파일에서 메타데이터 추출

    Returns:
        {
            "duration": 120.5,      # 초
            "sample_rate": 16000,   # Hz
            "channels": 1,          # mono/stereo
            "format": "wav"
        }
    """
    # librosa로 로드
    y, sr = librosa.load(file_path, sr=None)
    duration = librosa.get_duration(y=y, sr=sr)

    # soundfile로 채널 정보
    info = sf.info(file_path)

    return {
        "duration": duration,
        "sample_rate": sr,
        "channels": info.channels,
        "format": file_path.split('.')[-1]
    }
```

**대안: FFmpeg 사용 (더 가벼움)**
```python
import subprocess
import json

def extract_metadata_ffmpeg(file_path: str) -> dict:
    """FFmpeg로 메타데이터 추출"""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)

    audio_stream = next(s for s in data['streams'] if s['codec_type'] == 'audio')

    return {
        "duration": float(data['format']['duration']),
        "sample_rate": int(audio_stream['sample_rate']),
        "channels": int(audio_stream['channels']),
        "format": data['format']['format_name']
    }
```

**선택 기준:**
- librosa: 더 많은 기능 (스펙트로그램 등), 무거움
- FFmpeg: 가벼움, 시스템 의존성 필요

**권장:** librosa (Python 생태계 일관성)

---

### 4. Silero VAD 통합

**목적:** 음성 구간만 탐지하여 처리 시간 단축

**파일:** `backend/app/models/vad.py` 업데이트

```python
import torch
from typing import List

class VADModel(BaseModel):
    def __init__(self):
        super().__init__()
        self.model = None
        self.sampling_rate = 16000

    async def load(self):
        """Silero VAD 모델 로드"""
        self.model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False
        )
        self._loaded = True

    async def detect(self, audio_path: str) -> VADResult:
        """음성 구간 탐지"""
        import librosa

        # 오디오 로드 (16kHz로 리샘플링)
        audio, sr = librosa.load(audio_path, sr=self.sampling_rate)

        # Torch tensor로 변환
        audio_tensor = torch.from_numpy(audio)

        # VAD 실행
        speech_timestamps = get_speech_timestamps(
            audio_tensor,
            self.model,
            sampling_rate=self.sampling_rate
        )

        # 결과 변환
        segments = [
            VADSegment(
                start=ts['start'] / self.sampling_rate,
                end=ts['end'] / self.sampling_rate,
                confidence=1.0  # Silero는 confidence 미제공
            )
            for ts in speech_timestamps
        ]

        return VADResult(
            speech_segments=segments,
            total_speech_duration=sum(s.end - s.start for s in segments),
            processing_time=...
        )
```

**의존성:**
```toml
torch = "^2.0.0"         # Silero VAD 의존성
torchaudio = "^2.0.0"    # 오디오 처리
```

**M4 Mac 고려사항:**
- Torch는 MPS (Metal Performance Shaders) 지원
- CPU로도 충분히 빠름 (VAD는 경량 모델)

---

### 5. 프론트엔드 업로드 UI

**파일:** `frontend/src/components/AudioUpload.tsx` (새로 생성)

```typescript
import { useState } from 'react'
import { api } from '../services/api'

export function AudioUpload() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    try {
      const response = await api.uploadAudio(file)
      console.log('Uploaded:', response)
      // TODO: 업로드 성공 UI 표시
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="upload-container">
      <div
        className="dropzone"
        onDrop={(e) => {
          e.preventDefault()
          setFile(e.dataTransfer.files[0])
        }}
        onDragOver={(e) => e.preventDefault()}
      >
        {file ? (
          <p>{file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)</p>
        ) : (
          <p>Drag & Drop audio file here or click to select</p>
        )}
      </div>

      <input
        type="file"
        accept="audio/*"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />

      <button onClick={handleUpload} disabled={!file || uploading}>
        {uploading ? `Uploading... ${progress}%` : 'Upload'}
      </button>
    </div>
  )
}
```

**App.tsx 업데이트:**
```typescript
import { AudioUpload } from './components/AudioUpload'

function App() {
  return (
    <div className="app">
      <header>...</header>

      <main>
        <AudioUpload />  {/* 새로 추가 */}
        <StatusSection />
      </main>
    </div>
  )
}
```

---

## 📊 Phase 2 성공 기준

### 최소 요구사항 (MVP)
- [ ] 음성 파일 업로드 → `data/uploads/` 저장
- [ ] 데이터베이스에 메타데이터 기록
- [ ] duration, sample_rate, channels 자동 추출
- [ ] 프론트엔드에서 파일 선택 → 업로드 가능

### 선택 사항
- [ ] VAD로 음성 구간 탐지
- [ ] 진행률 표시 (업로드 중)
- [ ] 업로드된 파일 목록 표시

---

## 🔧 의존성 추가

```bash
cd backend
poetry add librosa soundfile torch torchaudio
```

**예상 설치 시간:** 5~10분 (Torch가 큼)

**용량:** ~2GB (Torch + 의존성)

---

## 🧪 테스트 계획

### 1. 파일 업로드 테스트

```bash
# 테스트 오디오 파일 준비
curl -o test_audio.wav "https://example.com/sample.wav"

# 업로드 테스트
curl -X POST http://localhost:8003/api/audio/upload \
  -F "file=@test_audio.wav"
```

### 2. 메타데이터 추출 테스트

```python
from app.utils.audio import extract_audio_metadata

metadata = extract_audio_metadata("data/uploads/test.wav")
assert metadata['duration'] > 0
assert metadata['sample_rate'] in [16000, 22050, 44100, 48000]
```

### 3. VAD 테스트

```python
from app.models.vad import VADModel

model = VADModel()
await model.load()

result = await model.detect("data/uploads/test.wav")
assert len(result.speech_segments) > 0
```

---

## 📝 다음 단계 (Phase 3)

Phase 2 완료 후:
1. ASR 모델 선택 (MLX Whisper vs faster-whisper 벤치마크)
2. 실제 전사 기능 구현
3. 평가 시스템 활성화

---

## 🚨 주의사항

### 1. 파일 크기 제한
- 현재 설정: 500MB (config.py)
- 큰 파일은 청크 단위 업로드 고려

### 2. 파일 포맷 지원
- 우선 지원: WAV, MP3, M4A, FLAC
- librosa가 자동으로 변환

### 3. 보안
- 파일 업로드는 로컬 환경만 가정
- 프로덕션 배포 시 추가 검증 필요

---

**작성자:** Claude Code
**검토:** Phase 2 시작 전
**다음 문서:** `phase2-completion-report.md` (완료 후 작성)

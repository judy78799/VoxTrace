# Phase 3: ASR 모델 통합

**시작일:** 2026-11-18
**상태:** 🚀 진행 예정

---

## 🎯 목표

Phase 2에서 구축한 오디오 파일 업로드 파이프라인 위에 **실제 음성 인식 모델**을 통합합니다.

### 핵심 기능
1. 🎤 실제 음성 → 텍스트 변환 (ASR)
2. 🕐 타임스탬프 생성 (세그먼트별)
3. 📊 신뢰도 점수 계산
4. 🇰🇷 한국어 최적화
5. 🧪 모델 성능 벤치마크

---

## 📋 ASR 모델 비교

### 옵션 1: MLX Whisper ⭐ **추천 (M4 Mac 최적화)**

**장점:**
- ✅ **Apple Silicon 최적화**: M4 칩의 Neural Engine 활용
- ✅ **낮은 메모리 사용**: Unified Memory 효율적 활용
- ✅ **빠른 추론 속도**: Metal 가속
- ✅ **Python 통합 용이**: `mlx-whisper` 패키지
- ✅ **최신 Whisper 모델**: OpenAI Whisper v3 지원

**단점:**
- ⚠️ macOS 전용 (배포 환경 제한)
- ⚠️ 상대적으로 새로운 프레임워크 (커뮤니티 작음)

**설치:**
```bash
poetry add mlx-whisper
```

**메모리 사용량 (M4 16GB 기준):**
- tiny: ~1GB
- base: ~1.5GB
- small: ~2.5GB
- medium: ~5GB ✅ **권장**
- large: ~10GB (여유있을 때만)

**처리 속도 추정 (M4 Pro):**
- medium 모델: RTF ~0.1-0.2 (1분 오디오 → 6-12초 처리)
- small 모델: RTF ~0.05-0.1 (1분 오디오 → 3-6초 처리)

---

### 옵션 2: faster-whisper

**장점:**
- ✅ CPU/GPU 모두 최적화 (CTranslate2)
- ✅ 크로스 플랫폼 (Linux, Windows, macOS)
- ✅ 성숙한 프레임워크, 큰 커뮤니티
- ✅ 메모리 효율적 (int8 양자화)

**단점:**
- ❌ M4 Neural Engine 미활용
- ❌ Metal 가속 없음 (CPU만 사용)
- ⚠️ 메모리 사용량이 MLX보다 약간 높음

**설치:**
```bash
poetry add faster-whisper
```

---

### 옵션 3: Transformers (Hugging Face)

**장점:**
- ✅ 표준 라이브러리
- ✅ 다양한 모델 지원

**단점:**
- ❌ 느린 추론 속도
- ❌ 높은 메모리 사용량
- ❌ 최적화 부족

**결론: 사용 안 함**

---

## ✅ 선택: **MLX Whisper**

**이유:**
1. M4 Mac에 최적화되어 최고 성능
2. 메모리 16GB로 medium 모델까지 충분히 실행 가능
3. 개발 환경(macOS)에서 최적의 사용자 경험
4. 프로덕션 배포는 Phase 7에서 고려 (필요시 faster-whisper로 전환 가능)

**선택 모델:** `medium` (한국어 성능 우수, 메모리 ~5GB)

---

## 📋 작업 목록

### 1. 의존성 추가 및 모델 다운로드

**패키지 설치:**
```bash
cd backend
poetry add mlx-whisper
```

**모델 다운로드:**
MLX Whisper는 첫 실행 시 자동으로 모델을 다운로드합니다.
- 위치: `~/.cache/huggingface/hub/`
- medium 모델 크기: ~1.5GB

**선택 가능 모델:**
- `tiny`: 39M params (빠르지만 정확도 낮음)
- `base`: 74M params
- `small`: 244M params
- `medium`: 769M params ✅ **권장**
- `large-v3`: 1550M params (메모리 충분할 때)

---

### 2. ASR 모델 클래스 구현

**파일:** `backend/app/models/asr.py`

```python
import mlx_whisper
from typing import List, Optional
from pathlib import Path

from app.schemas.audio import TranscriptionSegment, TranscriptionResult


class ASRModel:
    """
    MLX Whisper 기반 음성 인식 모델

    M4 Mac Neural Engine 최적화
    """

    def __init__(self, model_name: str = "medium"):
        self.model_name = model_name
        self.model = None
        self._loaded = False

    async def load(self):
        """모델 로딩 (첫 실행 시 다운로드)"""
        if self._loaded:
            return

        print(f"🔄 Loading MLX Whisper model: {self.model_name}...")

        # MLX Whisper 모델 로드 (Metal 가속 자동 활성화)
        self.model = mlx_whisper.load_model(self.model_name)
        self._loaded = True

        print(f"✅ MLX Whisper {self.model_name} loaded")

    async def transcribe(
        self,
        audio_path: str,
        language: str = "ko",
        task: str = "transcribe",
    ) -> TranscriptionResult:
        """
        음성 파일을 텍스트로 변환

        Args:
            audio_path: 오디오 파일 경로
            language: 언어 코드 (ko, en, etc.)
            task: "transcribe" 또는 "translate"

        Returns:
            TranscriptionResult with segments
        """
        if not self._loaded:
            await self.load()

        # Transcribe with MLX Whisper
        result = mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo=self.model_name,
            language=language,
            task=task,
            word_timestamps=False,  # 단어별 타임스탬프 (선택)
            verbose=False,
        )

        # Convert to our schema
        segments = [
            TranscriptionSegment(
                start=seg["start"],
                end=seg["end"],
                text=seg["text"].strip(),
                speaker=None,  # Diarization 없음 (Phase 4)
                confidence=seg.get("avg_logprob", 0.0),  # 로그 확률을 신뢰도로 사용
            )
            for seg in result["segments"]
        ]

        return TranscriptionResult(
            segments=segments,
            language=result["language"],
            full_text=result["text"].strip(),
        )

    async def unload(self):
        """모델 언로드 (메모리 해제)"""
        if self._loaded:
            self.model = None
            self._loaded = False
            print(f"🗑️  MLX Whisper {self.model_name} unloaded")
```

---

### 3. API 엔드포인트 업데이트

**파일:** `backend/app/api/audio.py`

**Before (Phase 2):**
```python
@router.post("/transcribe", response_model=TranscriptionResult)
async def transcribe_audio(request: TranscriptionRequest):
    # Dummy response
    return TranscriptionResult(...)
```

**After (Phase 3):**
```python
from app.models.asr import ASRModel
from app.db.models import AudioFile, Transcript, TranscriptSegment

# Global model instance (lazy loading)
asr_model = ASRModel(model_name="medium")

@router.post("/transcribe", response_model=TranscriptionResult)
async def transcribe_audio(
    request: TranscriptionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    실제 음성 인식 수행
    """
    import time

    # 1. 오디오 파일 조회
    result = await db.execute(
        select(AudioFile).where(AudioFile.id == request.file_id)
    )
    audio_file = result.scalar_one_or_none()

    if not audio_file:
        raise HTTPException(status_code=404, detail="Audio file not found")

    # 2. 모델 로딩 (첫 요청 시만)
    await asr_model.load()

    # 3. 음성 인식 수행
    start_time = time.time()

    transcription = await asr_model.transcribe(
        audio_path=audio_file.original_path,
        language=request.language,
    )

    processing_time = time.time() - start_time

    # 4. 데이터베이스에 저장
    transcript = Transcript(
        id=str(uuid.uuid4()),
        audio_file_id=audio_file.id,
        model_name="mlx-whisper",
        model_version="medium",
        language=request.language,
        diarization_enabled=request.enable_diarization,
        enhancement_enabled=request.enable_enhancement,
        processing_time=processing_time,
        created_at=datetime.now(),
    )
    db.add(transcript)

    # 세그먼트 저장
    for idx, seg in enumerate(transcription.segments):
        segment = TranscriptSegment(
            id=str(uuid.uuid4()),
            transcript_id=transcript.id,
            start_time=seg.start,
            end_time=seg.end,
            original_text=seg.text,
            confidence=seg.confidence,
            speaker=seg.speaker,
            edited_text=None,
            is_edited=False,
            segment_index=idx,
        )
        db.add(segment)

    await db.commit()

    # 5. 응답 반환
    return TranscriptionResult(
        file_id=audio_file.id,
        segments=transcription.segments,
        language=transcription.language,
        processing_time=processing_time,
        model_version="medium",
        created_at=datetime.now(),
    )
```

---

### 4. 스키마 업데이트

**파일:** `backend/app/schemas/audio.py`

**추가 필드:**
```python
class TranscriptionResult(BaseModel):
    file_id: str
    segments: List[TranscriptionSegment]
    language: str
    processing_time: float
    model_version: str
    created_at: datetime
    full_text: Optional[str] = None  # 전체 텍스트 추가
```

---

### 5. 프론트엔드 업데이트

**파일:** `frontend/src/components/TranscriptionViewer.tsx` (새로 생성)

```typescript
interface TranscriptionViewerProps {
  fileId: string
}

export function TranscriptionViewer({ fileId }: TranscriptionViewerProps) {
  const [result, setResult] = useState<TranscriptionResult | null>(null)
  const [loading, setLoading] = useState(false)

  const handleTranscribe = async () => {
    setLoading(true)
    try {
      const result = await api.transcribeAudio(fileId)
      setResult(result)
    } catch (error) {
      console.error('Transcription failed:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="transcription-viewer">
      <button onClick={handleTranscribe} disabled={loading}>
        {loading ? '전사 중...' : '음성 인식 시작'}
      </button>

      {result && (
        <div className="transcript">
          <h3>전사 결과</h3>
          <div className="full-text">{result.full_text}</div>

          <h4>세그먼트 ({result.segments.length})</h4>
          {result.segments.map((seg, idx) => (
            <div key={idx} className="segment">
              <span className="timestamp">
                {formatTime(seg.start)} - {formatTime(seg.end)}
              </span>
              <span className="text">{seg.text}</span>
              <span className="confidence">
                {(seg.confidence * 100).toFixed(1)}%
              </span>
            </div>
          ))}

          <div className="meta">
            <p>언어: {result.language}</p>
            <p>처리 시간: {result.processing_time.toFixed(2)}초</p>
            <p>모델: {result.model_version}</p>
          </div>
        </div>
      )}
    </div>
  )
}
```

---

## 🧪 테스트 계획

### 1. 모델 로딩 테스트

```bash
# Python 직접 실행
poetry run python -c "
import mlx_whisper
model = mlx_whisper.load_model('medium')
print('✅ Model loaded successfully')
"
```

### 2. 간단한 음성 인식 테스트

```python
# test_asr.py
import asyncio
from app.models.asr import ASRModel

async def test():
    model = ASRModel("medium")
    await model.load()

    result = await model.transcribe("data/uploads/test_audio.wav", language="ko")
    print(f"✅ Transcription: {result.full_text}")
    print(f"   Segments: {len(result.segments)}")

asyncio.run(test())
```

### 3. API 엔드포인트 테스트

```bash
# 1. 파일 업로드
FILE_ID=$(curl -X POST http://localhost:8003/api/audio/upload \
  -F "file=@test_korean.wav" | jq -r '.file_id')

# 2. 전사 요청
curl -X POST http://localhost:8003/api/audio/transcribe \
  -H "Content-Type: application/json" \
  -d "{\"file_id\": \"$FILE_ID\", \"language\": \"ko\"}" | jq .
```

### 4. 성능 벤치마크

**측정 항목:**
- RTF (Real-Time Factor): processing_time / audio_duration
- Peak Memory Usage (psutil)
- Accuracy (CER) - Ground Truth 필요

---

## 📊 Phase 3 성공 기준

### 필수 요구사항
- [ ] MLX Whisper medium 모델 로딩 성공
- [ ] 실제 한국어 음성 → 텍스트 변환 작동
- [ ] 타임스탬프 정확도 ±0.5초 이내
- [ ] 데이터베이스에 전사 결과 저장
- [ ] 프론트엔드에서 결과 표시

### 성능 목표
- [ ] RTF < 0.3 (1분 오디오 → 18초 이내 처리)
- [ ] Peak Memory < 8GB (16GB의 50% 이하)
- [ ] CER < 15% (한국어, 깨끗한 음성 기준)

---

## ⚠️ 예상 문제 및 해결책

### 1. 모델 다운로드 실패
**증상:** Hugging Face 연결 실패
**해결:** 수동 다운로드 또는 프록시 설정

### 2. 메모리 부족 (OOM)
**증상:** 처리 중 프로그램 종료
**해결:** 모델 크기 축소 (medium → small)

### 3. 느린 처리 속도
**증상:** RTF > 0.5
**해결:**
- 긴 오디오는 청크 단위 처리
- VAD로 무음 제거 (Phase 2 완료 후)

### 4. 한국어 인식 정확도 낮음
**증상:** CER > 20%
**해결:**
- 모델 크기 증가 (medium → large)
- 오디오 품질 향상 (enhancement)
- Prompt 튜닝

---

## 📝 다음 단계 (Phase 4)

Phase 3 완료 후:
1. **Speaker Diarization** (pyannote.audio)
   - 화자 분리 및 라벨링
   - "SPEAKER_00", "SPEAKER_01" 태그

2. **Audio Enhancement** (DeepFilterNet)
   - 노이즈 제거
   - 저음질 오디오 개선

3. **Transcript Editor** (프론트엔드)
   - 수동 수정 UI
   - 변경 이력 추적

---

**작성자:** Claude Code
**검토 필요:** Phase 3 시작 전
**다음 문서:** `phase3-completion-report.md` (완료 후 작성)

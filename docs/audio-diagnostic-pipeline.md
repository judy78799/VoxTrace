# Audio Diagnostic Pipeline

음성 인식 실패 원인 분류 및 데이터 품질 분석 시스템

## 개요

VoxTrace의 Audio Diagnostic Pipeline은 음성 파일의 음향적 특성을 측정하고 품질 문제를 정의하여, STT 성능 저하의 원인을 체계적으로 분석합니다.

## 분석 항목

| 항목 | 측정 내용 | 목적 |
|------|-----------|------|
| **Duration** | 음성 길이 | 처리 시간 및 데이터 분포 |
| **Sample Rate** | 16kHz, 44.1kHz, 48kHz | 모델 입력 조건 확인 |
| **Channels** | Mono / Stereo | 채널별 음성 분석 |
| **RMS / Loudness** | 평균 음량 | 음성 크기 확인 |
| **Peak Amplitude** | 최대 진폭 | Clipping 여부 |
| **Clipping Ratio** | 잘린 파형 비율 | 왜곡 여부 |
| **SNR** | 음성과 노이즈의 비율 | 노이즈 심각도 |
| **VAD** | Speech / Non-speech 구간 | 실제 발화 구간 추출 |
| **Speech Ratio** | 전체 중 음성 비율 | 불필요한 구간 처리 |
| **Spectrogram** | 주파수별 에너지 | 노이즈 및 음성 특성 |
| **Reverberation** | 잔향 정도 | 공간 울림 문제 |
| **Overlap** | 다중 화자 중첩 | 화자 간 분리 필요성 |

## 아키텍처

```
① 원본 음성 (Raw Audio)
   ↓
② Audio Quality Analysis
   - SNR 계산
   - VAD 기반 음성 비율
   - Clipping 감지
   - Reverberation 추정
   - Speech Detection
   ↓
③ 문제 유형 분류
   - Noise Level: low / medium / high / very_high
   - Reverberation: none / low / medium / high
   - Speech Quality: excellent / good / fair / poor
   - Quality Issues: [구체적 문제 목록]
   ↓
④ 문제별 개선 전략 제안
   - 조건에 맞는 처리기 선택
   - 또는 원본 유지 권장
   ↓
⑤ STT Inference
   - 원본 및 전처리 음성 전사
   ↓
⑥ Confidence & Error Analysis
   - 결과 비교
   - 저신뢰 구간 검출
   - 재처리 권장
```

## API 사용법

### 1. 음성 파일 업로드

```bash
curl -X POST "http://localhost:8000/audio/upload" \
  -F "file=@recording.wav"
```

응답:
```json
{
  "file_id": "abc-123",
  "filename": "recording.wav",
  "duration": 125.4,
  "sample_rate": 48000,
  "channels": 2
}
```

### 2. 전사 + 품질 분석 (자동)

```bash
curl -X POST "http://localhost:8000/audio/transcribe" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "abc-123",
    "enable_vad": true,
    "enable_diarization": false,
    "enable_enhancement": false,
    "language": "ko"
  }'
```

**중요**: 전사 요청 시 품질 분석이 자동으로 실행되고 DB에 저장됩니다.

### 3. 품질 분석 결과 조회

```bash
curl "http://localhost:8000/audio/file/abc-123/quality-analysis"
```

응답 예시:
```json
{
  "file_name": "recording_001.wav",
  "file_id": "abc-123",
  "duration": 125.4,
  "sample_rate": 48000,
  "channels": 2,

  "speech_ratio": 0.68,
  "speech_segments_count": 42,

  "estimated_snr_db": 4.2,
  "noise_level": "high",

  "clipping_detected": true,
  "clipping_ratio": 0.001,

  "reverberation_level": "medium",
  "reverberation_time_ms": 300,

  "overlapping_speech": false,
  "overlapping_speech_ratio": null,

  "quality_score": 52.0,
  "speech_quality": "fair",
  "quality_issues": {
    "issues": [
      "낮은 SNR (4.2 dB) - 배경 소음이 큽니다",
      "클리핑 감지 (0.10%)",
      "중간 잔향 - 약간의 울림"
    ]
  },

  "frequency_analysis": {
    "low_freq_energy": 0.123,
    "mid_freq_energy": 0.456,
    "high_freq_energy": 0.089,
    "spectral_centroid": 1250.5,
    "spectral_rolloff": 3200.0,
    "spectral_bandwidth": 1800.0
  },

  "rms_energy": 0.0234,
  "zero_crossing_rate": 0.145,

  "analyzed_at": "2026-11-22T12:00:00",
  "analysis_version": "1.0.0"
}
```

## 품질 판정 기준

### Speech Quality

- **excellent** (80-100점): 깨끗한 음성, 최소 노이즈, 왜곡 없음
- **good** (65-79점): 약간의 배경 소음, 전사 가능
- **fair** (45-64점): 중간 수준 노이즈, 일부 구간 불명확
- **poor** (0-44점): 높은 노이즈, 왜곡, 전사 어려움

### Noise Level

- **low**: SNR > 20 dB
- **medium**: 15 dB < SNR ≤ 20 dB
- **high**: 10 dB < SNR ≤ 15 dB
- **very_high**: SNR ≤ 10 dB

### Reverberation Level

- **none**: RT60 < 100ms
- **low**: 100ms ≤ RT60 < 200ms
- **medium**: 200ms ≤ RT60 < 400ms
- **high**: RT60 ≥ 400ms

## 데이터베이스 스키마

### audio_quality_analysis 테이블

```sql
CREATE TABLE audio_quality_analysis (
    id TEXT PRIMARY KEY,
    audio_file_id TEXT UNIQUE NOT NULL,

    -- 기본 메타데이터
    duration REAL NOT NULL,
    sample_rate INTEGER NOT NULL,
    channels INTEGER NOT NULL,

    -- SNR 분석
    snr_db REAL,

    -- 주파수 분석
    low_freq_energy REAL,
    mid_freq_energy REAL,
    high_freq_energy REAL,
    spectral_centroid REAL,
    spectral_rolloff REAL,
    spectral_bandwidth REAL,

    -- 클리핑/왜곡
    clipping_detected BOOLEAN DEFAULT 0,
    clipping_ratio REAL DEFAULT 0.0,

    -- 에너지 지표
    rms_energy REAL NOT NULL,
    zero_crossing_rate REAL NOT NULL,

    -- VAD 분석
    speech_ratio REAL,
    speech_segments_count INTEGER,

    -- 잔향
    reverberation_level TEXT,
    reverberation_time_ms REAL,

    -- 화자 중첩
    overlapping_speech_detected BOOLEAN DEFAULT 0,
    overlapping_speech_ratio REAL,

    -- 품질 평가
    quality_score REAL NOT NULL,
    quality_issues JSON,
    noise_level TEXT,
    speech_quality TEXT,

    -- 메타데이터
    analyzed_at TIMESTAMP NOT NULL,
    analysis_version TEXT DEFAULT '1.0.0'
);
```

## 구현 세부사항

### AudioAnalysisModel

위치: `backend/app/models/audio_analysis.py`

**주요 기능:**
- SNR 계산 (상위 50% vs 하위 20% RMS 에너지 비율)
- 주파수 분석 (저/중/고 대역별 에너지)
- 클리핑 감지 (99% 임계값 초과 샘플)
- VAD 기반 음성 비율 (Silero VAD 활용)
- 잔향 추정 (에너지 감쇄율 기반)
- 화자 중첩 감지 (스펙트럼 플럭스 기반)

### VAD 통합

```python
# VAD 모델을 audio_analysis_model에 전달
audio_analysis_model = AudioAnalysisModel(vad_model=vad_model)

# 분석 시 VAD 활용
analysis_result = await audio_analysis_model.analyze(
    audio_path="file.wav",
    enable_vad_analysis=True,  # 음성 비율 계산
    enable_reverberation=True,
    enable_overlap_detection=False,  # 느려서 선택적
)
```

## 활용 방안

### 1. 전처리 전략 선택

```python
if quality_analysis.noise_level in ["high", "very_high"]:
    # DeepFilterNet 적용
    apply_noise_reduction()

if quality_analysis.reverberation_level in ["medium", "high"]:
    # WPE 적용
    apply_dereverberation()

if quality_analysis.clipping_detected:
    # 원본 유지 권장 (복구 불가능)
    warn_user("Clipping detected - enhancement may not help")
```

### 2. STT 모델 선택

```python
if quality_analysis.speech_quality in ["excellent", "good"]:
    # 빠른 모델 사용 가능
    use_model("whisper-medium")
else:
    # 더 강력한 모델 필요
    use_model("whisper-large-v3")
```

### 3. 데이터셋 필터링

```python
# 평가 데이터셋 구축 시
if quality_analysis.quality_score >= 70:
    add_to_clean_dataset()
elif 40 <= quality_analysis.quality_score < 70:
    add_to_noisy_dataset()
else:
    add_to_very_noisy_dataset()
```

### 4. 성능 분석

```python
# 품질별 CER/WER 비교
for quality_level in ["excellent", "good", "fair", "poor"]:
    files = filter_by_speech_quality(quality_level)
    avg_cer = calculate_average_cer(files)
    print(f"{quality_level}: CER = {avg_cer:.2f}%")
```

## 메모리 최적화

### 단계별 로딩

```python
# 1. 경량 분석 (librosa, numpy)
audio_analysis = await audio_analysis_model.analyze(...)  # ~100MB

# 2. VAD 필요시에만 로드
if enable_vad_analysis:
    await vad_model.load()  # ~100MB
    # 분석 완료 후
    await vad_model.unload()

# 3. ASR 로드 (가장 무거움)
await asr_model.load()  # 1.5-3GB
# 전사 완료 후
await asr_model.unload()
```

## 향후 개선 방향

1. **실제 RT60 측정**: 현재는 간단한 에너지 감쇄율 기반 → impulse response 분석
2. **정확한 화자 중첩 감지**: pyannote.audio 통합 (현재는 근사값)
3. **음질 분류 모델**: 머신러닝 기반 품질 예측
4. **자동 개선 추천**: 품질 분석 → 최적 전처리 조합 추천
5. **실시간 분석**: 긴 파일에 대한 청크 단위 분석

## 참고 자료

- 프로젝트 구조: `/docs/phase1-completion-report.md`
- DB 스키마: `backend/app/db/models.py`
- 평가 시스템: `backend/app/evaluation/`
- CLAUDE.md 원칙: "투명한 불확실성", "실험적 비교"

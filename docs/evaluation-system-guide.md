# VoxTrace 평가 시스템 가이드

**작성일:** 2026-11-16
**목적:** 모델 성능을 객관적으로 측정하고 비교하기 위한 평가 시스템

---

## 📊 평가 지표 개요

VoxTrace는 **저음질 음성 견고 인식**을 목표로 하므로, 단순한 정확도뿐만 아니라 처리 속도와 리소스 사용량도 중요합니다.

### 주요 평가 지표

| 지표 | 설명 | 목표 | 비고 |
|------|------|------|------|
| **CER** | Character Error Rate (문자 오류율) | ↓ 낮을수록 좋음 | **주 지표** (한국어 적합) |
| **WER** | Word Error Rate (어절 오류율) | ↓ 낮을수록 좋음 | 보조 지표 (띄어쓰기 영향) |
| **DER** | Diarization Error Rate (화자 분리 오류율) | ↓ 낮을수록 좋음 | Phase 4+ |
| **RTF** | Real-Time Factor (실시간 계수) | ↓ 낮을수록 좋음 | <1.0이면 실시간보다 빠름 |
| **Peak RAM** | 최대 메모리 사용량 (MB) | ↓ 낮을수록 좋음 | M4 16GB 환경 고려 |

---

## 🗄️ 데이터베이스 스키마

### 1. `evaluation_datasets` - Ground Truth 관리

**사용자가 수동으로 검수한 정답 데이터**

```sql
CREATE TABLE evaluation_datasets (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    audio_file_id VARCHAR(36) NOT NULL,
    ground_truth_text TEXT NOT NULL,      -- 정답 전사 텍스트
    audio_quality VARCHAR(20) NOT NULL,   -- 'clean', 'noisy', 'reverberant', 'very_noisy'
    noise_level VARCHAR(20),              -- 'low', 'medium', 'high'
    reverb_level VARCHAR(20),             -- 'none', 'low', 'medium', 'high'
    num_speakers INTEGER,
    language VARCHAR(10) DEFAULT 'ko',
    tags JSON,                            -- ["interview", "meeting", "phone"]
    created_at DATETIME,
    verified_by VARCHAR(100)
);
```

**사용 예시:**
```python
# Ground Truth 추가
dataset = EvaluationDataset(
    id="eval-001",
    name="회의 녹음 샘플 1",
    audio_file_id="audio-123",
    ground_truth_text="오늘 회의는 오후 3시에 시작합니다",
    audio_quality="noisy",
    noise_level="medium",
    num_speakers=2,
    verified_by="user",
)
```

---

### 2. `experiment_configs` - 실험 조건 설정

**동일 오디오에 대해 다양한 전처리/모델 조합 테스트**

```sql
CREATE TABLE experiment_configs (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    preprocessing JSON,                  -- {"noise_reduction": true, "dereverberation": true}
    asr_model VARCHAR(100) NOT NULL,     -- 'mlx-whisper-small', 'faster-whisper-base'
    asr_version VARCHAR(50) NOT NULL,
    asr_params JSON,
    diarization_enabled BOOLEAN DEFAULT FALSE,
    diarization_model VARCHAR(100),
    created_at DATETIME
);
```

**실험 시나리오 예시:**

| Experiment ID | 이름 | 전처리 | ASR 모델 |
|--------------|------|-------|---------|
| exp-A | 원본 + Whisper Small | 없음 | mlx-whisper-small |
| exp-B | 잡음제거 + Whisper Small | noise_reduction | mlx-whisper-small |
| exp-C | 잔향제거 + Whisper Small | dereverberation | mlx-whisper-small |
| exp-D | 복합전처리 + Whisper Small | noise + reverb | mlx-whisper-small |
| exp-E | 원본 + Faster Whisper | 없음 | faster-whisper-base |

---

### 3. `evaluations` - 평가 결과 저장

```sql
CREATE TABLE evaluations (
    id VARCHAR(36) PRIMARY KEY,
    experiment_config_id VARCHAR(36) NOT NULL,
    dataset_id VARCHAR(36) NOT NULL,
    transcript_id VARCHAR(36) NOT NULL,

    -- ASR 지표
    cer FLOAT,                           -- Character Error Rate
    wer FLOAT,                           -- Word Error Rate
    substitutions INTEGER,                -- 치환 오류
    deletions INTEGER,                    -- 삭제 오류
    insertions INTEGER,                   -- 삽입 오류

    -- 화자 분리 지표 (Phase 4+)
    der FLOAT,                           -- Diarization Error Rate
    jer FLOAT,                           -- Jaccard Error Rate
    miss_rate FLOAT,                     -- Missed speech
    false_alarm_rate FLOAT,              -- False detection
    confusion_rate FLOAT,                -- Speaker confusion

    -- 성능 지표
    rtf FLOAT,                           -- Real-Time Factor
    processing_time FLOAT,               -- 총 처리 시간 (초)
    model_load_time FLOAT,               -- 모델 로딩 시간
    first_token_time FLOAT,              -- 첫 결과까지 시간

    -- 리소스 사용량
    peak_memory_mb FLOAT,                -- 최대 메모리 (MB)
    avg_memory_mb FLOAT,                 -- 평균 메모리
    cpu_usage_percent FLOAT,             -- 평균 CPU %
    gpu_usage_percent FLOAT,             -- 평균 GPU %

    audio_duration FLOAT,                -- 음성 길이 (초)
    notes TEXT,
    error_log TEXT,
    created_at DATETIME
);
```

---

### 4. `model_benchmarks` - 모델별 종합 성능

여러 평가 결과를 집계한 모델의 전체 성능 요약

```sql
CREATE TABLE model_benchmarks (
    id VARCHAR(36) PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) NOT NULL,     -- 'asr', 'diarization', 'enhancement'

    num_evaluations INTEGER NOT NULL,     -- 평가 횟수
    avg_cer FLOAT,                        -- 평균 CER
    avg_wer FLOAT,
    avg_der FLOAT,
    avg_rtf FLOAT,
    avg_peak_memory_mb FLOAT,

    metrics_by_quality JSON,              -- 음질별 성능
    hardware VARCHAR(200) NOT NULL,       -- 'M4 Mac 16GB'

    created_at DATETIME,
    updated_at DATETIME
);
```

**예시 데이터:**
```json
{
  "model_name": "mlx-whisper-small",
  "avg_cer": 12.5,
  "avg_rtf": 0.35,
  "metrics_by_quality": {
    "clean": {"cer": 5.2, "wer": 8.1},
    "noisy": {"cer": 18.5, "wer": 25.3},
    "very_noisy": {"cer": 32.1, "wer": 45.2}
  }
}
```

---

## 🔧 평가 코드 사용법

### 1. CER / WER 계산

```python
from app.evaluation.metrics import calculate_cer, calculate_wer

# 정답 vs 예측
ground_truth = "오늘 회의는 오후 3시에 시작합니다"
prediction = "오늘 회의는 오후 세시에 시작합니다"

# CER 계산
cer_result = calculate_cer(ground_truth, prediction)
print(f"CER: {cer_result['cer']:.2%}")
print(f"Substitutions: {cer_result['substitutions']}")
print(f"Deletions: {cer_result['deletions']}")
print(f"Insertions: {cer_result['insertions']}")

# WER 계산
wer_result = calculate_wer(ground_truth, prediction)
print(f"WER: {wer_result['wer']:.2%}")
```

---

### 2. 모델 벤치마크 실행

```python
from app.models.asr import ASRModel
from app.evaluation.benchmark import BenchmarkRunner

# 모델 준비
model = ASRModel(model_name="mlx-whisper-small")
await model.load()

# 벤치마크 실행
benchmark = BenchmarkRunner(warmup_runs=1)

result = await benchmark.run_asr_benchmark(
    model=model,
    audio_path="test_audio.wav",
    ground_truth="오늘 회의는 오후 3시에 시작합니다"
)

print(f"CER: {result['cer']:.2%}")
print(f"WER: {result['wer']:.2%}")
print(f"RTF: {result['rtf']:.2f}")
print(f"Peak Memory: {result['resource_usage']['peak_memory_mb']:.1f} MB")
```

---

### 3. 여러 모델 비교

```python
# 두 모델 준비
model_mlx = ASRModel(model_name="mlx-whisper-small")
model_faster = ASRModel(model_name="faster-whisper-base")

await model_mlx.load()
await model_faster.load()

# 각각 벤치마크
result_mlx = await benchmark.run_asr_benchmark(model_mlx, "test.wav", "정답 텍스트")
result_faster = await benchmark.run_asr_benchmark(model_faster, "test.wav", "정답 텍스트")

# 비교
comparison = benchmark.compare_models({
    "MLX Whisper Small": result_mlx,
    "Faster Whisper Base": result_faster
})

print("=== 모델 비교 ===")
for model in comparison['comparison_table']:
    print(f"{model['model']:25} CER: {model['cer']:.1%}  RTF: {model['rtf']:.2f}  RAM: {model['peak_memory_mb']:.0f}MB")

print(f"\n최고 정확도: {comparison['best_accuracy']['model']} (CER {comparison['best_accuracy']['cer']:.1%})")
print(f"최고 속도: {comparison['best_speed']['model']} (RTF {comparison['best_speed']['rtf']:.2f})")
```

---

### 4. 리소스 모니터링

```python
from app.evaluation.benchmark import monitor_resources

with monitor_resources() as monitor:
    # 모델 실행
    result = await model.transcribe("audio.wav")

    # 주기적으로 샘플링
    monitor.sample()

usage = monitor.get_usage()
print(f"Peak Memory: {usage.peak_memory_mb:.1f} MB")
print(f"Avg Memory: {usage.avg_memory_mb:.1f} MB")
print(f"CPU Usage: {usage.cpu_percent:.1f}%")
print(f"Platform: {usage.platform_info}")
```

---

## 📁 평가 데이터 구조 (권장)

```
evaluation/
├── datasets/
│   ├── clean/
│   │   ├── sample_001.wav
│   │   └── sample_001.txt         # Ground truth
│   ├── noisy/
│   │   ├── interview_01.wav
│   │   └── interview_01.txt
│   └── reverberant/
│       ├── meeting_01.wav
│       └── meeting_01.txt
├── results/
│   ├── mlx_whisper_small.json     # 모델별 결과
│   ├── faster_whisper_base.json
│   └── comparison_report.md
└── benchmarks/
    └── m4_mac_16gb.json           # 하드웨어별 벤치마크
```

---

## 🎯 권장 평가 워크플로우

### Phase 3: ASR 모델 선택

```
1. Ground Truth 준비 (5~10개 샘플)
   ├── 깨끗한 음성 2개
   ├── 약간 잡음 3개
   ├── 심한 잡음 2개
   └── 잔향 있는 음성 2개

2. 모델 벤치마크
   ├── MLX Whisper Small
   ├── MLX Whisper Base
   ├── Faster Whisper Small
   └── Faster Whisper Base

3. 비교 기준
   ├── CER (주 지표)
   ├── RTF (처리 속도)
   └── Peak RAM (메모리)

4. 선택
   └── CER < 15% && RTF < 1.0 && RAM < 8GB 조건 만족하는 모델
```

---

### Phase 6: 전처리 효과 측정

```
1. 동일 오디오로 4가지 실험
   ├── A: 원본
   ├── B: 잡음 제거 (DeepFilterNet)
   ├── C: 잔향 제거 (WPE)
   └── D: 복합 전처리

2. 각 실험별 ASR 실행

3. CER 비교
   ├── A (baseline) vs B: 잡음 제거 효과
   ├── A vs C: 잔향 제거 효과
   └── A vs D: 복합 전처리 효과

4. 결론
   └── 전처리가 CER을 실제로 개선하는가?
```

---

## 📊 결과 시각화 (향후 구현)

```python
# Phase 5+에서 프론트엔드 구현 예정
# 비교 차트
- CER by audio quality (bar chart)
- RTF vs CER scatter plot
- Memory usage over time (line chart)
- Confusion matrix (diarization)
```

---

## ⚠️ 중요 원칙

### 1. Ground Truth는 신중하게
- **사람이 직접 검수한 정답 데이터만 사용**
- AI가 생성한 텍스트를 정답으로 쓰지 말 것
- 불확실한 구간은 별도 표시

### 2. 공정한 비교
- 동일한 오디오 파일 사용
- 동일한 환경 (온도, 백그라운드 프로세스)
- Warmup 실행 후 측정

### 3. 음질 분류 기준
- **clean**: SNR > 20dB, 잔향 없음
- **noisy**: SNR 10~20dB, 배경 잡음 있음
- **reverberant**: 실내 반향음 뚜렷함
- **very_noisy**: SNR < 10dB, 음성 식별 어려움

### 4. 평가 빈도
- 모델 변경 시: 필수
- 전처리 변경 시: 필수
- 정기 평가: 주 1회 (데이터셋 확장 시)

---

## 📝 다음 단계

- [ ] Phase 2: VAD 통합 후 음성 구간 탐지 정확도 평가
- [ ] Phase 3: ASR 모델 벤치마크 (MLX vs faster-whisper)
- [ ] Phase 4: DER 계산 구현 (pyannote.metrics)
- [ ] Phase 5: 프론트엔드 평가 대시보드
- [ ] Phase 6: 전처리 효과 A/B 테스트
- [ ] Phase 7: 최종 성능 리포트 생성

---

**관련 문서:**
- [Database Schema](./phase1-completion-report.md#데이터베이스-스키마)
- [기술적 결정](./DECISIONS.md)
- [CLAUDE.md - 평가 전략](../CLAUDE.md)

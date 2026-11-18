# VoxTrace 개발 가이드

**저음질 음성 견고 인식 시스템**

## 핵심 원칙

### 1. 데이터 무결성
- **원본 음성 파일을 절대 수정하지 않는다**
- 모든 음성 개선은 별도 파일로 생성
- 완전한 편집 이력 보존
- AI 예측과 사용자 확인 텍스트를 구분

### 2. 투명한 불확실성
> VoxTrace는 무엇을 알고 무엇을 모르는지 명확히 보여준다.
> 낮은 신뢰도 예측을 그럴듯한 문장으로 덮어쓰지 않는다.

- 신뢰도 점수 표시
- 불확실한 구간 강조
- 사용자 검증 허용
- 수정 패턴 추적

### 3. 실험적 비교
- 원본 vs 개선 음성 테스트
- CER/WER 객관적 측정
- 다양한 전처리 조합 비교
- 무엇이 효과적인지 문서화

## 아키텍처 개요

```
VoxTrace/
├── backend/           # FastAPI + Python
│   ├── app/
│   │   ├── api/       # REST 엔드포인트
│   │   ├── models/    # AI 모델 추상화
│   │   ├── db/        # SQLAlchemy 모델
│   │   ├── core/      # 설정 및 유틸리티
│   │   └── schemas/   # Pydantic 스키마
│   └── tests/
├── frontend/          # React + TypeScript
│   └── src/
│       ├── components/
│       ├── services/  # API 클라이언트
│       └── types/     # TypeScript 정의
└── data/              # 사용자 데이터 (git 제외)
    ├── uploads/       # 원본 음성
    ├── processed/     # 개선 음성
    └── db/            # SQLite 데이터베이스
```

## 개발 단계

### Phase 1: 기반 구축 ✅
- 프로젝트 구조
- API 엔드포인트 (더미 응답)
- 데이터베이스 스키마
- 모델 인터페이스 (실제 모델 없음)
- 기본 프론트엔드

### Phase 2: 음성 파이프라인
- 파일 업로드 및 검증
- 음성 분할 (긴 파일 → 청크)
- 타임스탬프 정렬
- VAD 통합 (Silero VAD)

### Phase 3: 한국어 ASR
**중요: 모델 선택**
- M4 Mac에서 MLX Whisper vs faster-whisper 테스트
- 벤치마크: 메모리 사용량, 속도, CER
- 가정이 아닌 데이터 기반 선택

### Phase 4: 화자 분리
- pyannote.audio 통합
- ASR과 병렬 실행
- 타임스탬프 기준 병합
- 겹치는 음성 처리

### Phase 5: 사용자 편집
- 전사 편집기 UI
- 편집 이력 추적
- 신뢰도 시각화
- 내보내기 형식 (txt, srt, vtt, json)

### Phase 6: 음성 개선
**기준선 확립 후에만 진행**
- DeepFilterNet (잡음 제거)
- WPE (잔향 제거)
- A/B 테스트: 원본 vs 개선
- CER/WER 개선도 측정

### Phase 7: 평가
- 정답 텍스트 비교
- CER/WER 계산 (jiwer)
- 음질 분류
- 성능 리포트

## 기술 결정

### 백엔드
- **FastAPI**: 비동기, 자동 문서화, Python 생태계
- **SQLite**: 로컬 우선, 설치 불필요
- **SQLAlchemy**: 비동기 지원 타입 안전 ORM
- **Pydantic**: 요청/응답 검증

### 프론트엔드
- **Vite**: 빠른 개발 서버 및 빌드
- **React**: 컴포넌트 기반 UI
- **TypeScript**: API 계약 타입 안전성

### 모델 (향후 단계)
| 모델 | 목적 | 상태 |
|------|------|------|
| MLX Whisper / faster-whisper | ASR | Phase 3 |
| pyannote.audio | 화자 분리 | Phase 4 |
| Silero VAD | 음성 구간 탐지 | Phase 2 |
| DeepFilterNet | 잡음 제거 | Phase 6 |
| WPE | 잔향 제거 | Phase 6 |

## 데이터베이스 설계 원칙

### 불변성
- `audio_files`: 원본 메타데이터 (절대 수정 안 함)
- `transcript_segments`: `original_text` 보존, `edited_text`는 사용자 수정용

### 감사 추적
- `transcript_edits`: 완전한 편집 이력
- `processed_audio`: 음성 개선 파라미터 추적
- `evaluations`: 시간별 성능 지표

### 스키마 주요 테이블
```sql
audio_files         → 원본 업로드 (불변)
processed_audio     → 개선된 변형
transcripts         → ASR 결과
transcript_segments → 개별 발화
transcript_edits    → 편집 이력
evaluations         → CER/WER 지표
```

## 개발 규칙

### 패키지 추가 시
1. 필요성 정당화 (기존 솔루션 대비)
2. M4 Mac 호환성 확인
3. pyproject.toml / package.json에 문서화
4. 고려한 대안 기록

### 인터페이스 변경 시
1. 데이터베이스 스키마 영향 확인
2. Pydantic 스키마 업데이트
3. TypeScript 타입 업데이트
4. 프론트엔드-백엔드 계약 테스트

### 모델 통합
1. 모델 로딩과 추론을 분리
2. 모델 미로딩 상태 우아하게 처리
3. 모델 언로딩 허용 (메모리 관리)
4. 결과에 모델 버전 기록

### Git 제외 항목
- `data/` - 사용자 프라이버시
- `models/` - 대용량 파일
- `*.db` - 로컬 상태

## 테스트 전략

### Phase 1
- ✅ 백엔드가 오류 없이 시작
- ✅ 프론트엔드가 API에 연결
- ✅ Health 엔드포인트 응답
- ✅ 더미 전사 동작

### Phase 2+
- 다양한 음성 포맷 업로드
- 긴 파일 분할 테스트
- 타임스탬프 정확도 검증
- 처리 속도 벤치마크

### Phase 3+
- 한국어 ASR 정확도 (CER < 15%)
- 다중 화자 처리
- 저음질 음성 견고성
- 음성 개선 A/B 비교

## M4 Mac 최적화

### 메모리 제약 (16GB)
- 모든 모델을 동시에 로딩하지 않기
- 지연 로딩 구현
- 모델 언로드 API 제공
- 메모리 사용량 모니터링

### MLX vs faster-whisper
**TODO: Phase 3 벤치마크**
- 분당 처리 속도
- 최대 메모리 사용량
- 테스트 데이터셋 CER
- 이론이 아닌 경험적 선택

## 연구 목표

이것은 단순한 STT 서비스가 아니다. 다음을 연구하는 프로젝트다:

1. **견고성**: 잡음, 잔향, 불명확한 음성에서 ASR이 얼마나 잘 작동하는가?
2. **개선 효과**: 전처리가 실제로 도움이 되는가, 해가 되는가?
3. **투명성**: AI가 확신하는 것을 사용자에게 보여줄 수 있는가?
4. **평가**: 실제 증거 녹취에서 어떤 지표가 중요한가?

## Phase 1 이후 다음 단계

1. 음성 업로드 및 저장 설정
2. Silero VAD 통합
3. 한국어 음성으로 Whisper 변형 벤치마크
4. 기본 전사 편집기 구현
5. 엔드투엔드 파이프라인 테스트
6. 그 후에 음성 개선 추가

---

**기억할 것**: 우리는 편의가 아닌 진실을 위한 도구를 만든다. 증거를 보존하고, 불확실성을 보여주며, 객관적으로 측정한다.

# VoxTrace

**저음질 음성 견고 인식 시스템**

잡음, 잔향, 도전적인 음성 환경에 특화된 로컬 우선 음성 인식 시스템. 증거 녹취, 인터뷰 등 음질을 예측할 수 없는 실제 상황을 위해 설계되었습니다.

## 주요 기능 (계획)

- 🎙️ **한국어 ASR** - 저음질 음성에 최적화
- 👥 **화자 분리** - 누가 무엇을 말했는지 식별
- 🔊 **음성 개선** - 잡음 제거, 잔향 제거
- ✏️ **대화형 편집** - 신뢰도 시각화
- 📊 **평가 지표** - CER/WER 품질 평가
- 🔒 **프라이버시 우선** - 모든 처리를 로컬에서 수행

## 프로젝트 상태

**Phase 1: 기반 구축** ✅

핵심 아키텍처 구축 완료. 모델은 아직 통합되지 않음.

## 빠른 시작

### 필수 요구사항

- Python 3.11+
- Node.js 18+
- pnpm (또는 npm)
- Poetry (Python 패키지 관리자)

### 설치

```bash
# 저장소 이동
cd VoxTrace

# 백엔드 설정
cd backend
poetry install
poetry shell

# 프론트엔드 설정 (다른 터미널)
cd frontend
pnpm install
```

### 로컬 실행

```bash
# 터미널 1: 백엔드
cd backend
poetry run uvicorn app.main:app --reload --port 8003

# 터미널 2: 프론트엔드
cd frontend
pnpm dev
```

http://localhost:5173 열기

### API 테스트

```bash
# Health check
curl http://localhost:8003/api/health

# API 문서
open http://localhost:8003/docs
```

## 아키텍처

```
┌─────────────┐
│  Frontend   │  React + TypeScript
│   (Vite)    │  전사 편집기, 음성 업로드
└──────┬──────┘
       │ HTTP/REST
┌──────▼──────┐
│   Backend   │  FastAPI + Python
│             │  음성 처리, ASR, 화자 분리
└──────┬──────┘
       │
┌──────▼──────┐
│   SQLite    │  프로젝트, 전사, 편집 이력
└─────────────┘
```

## 기술 스택

| 구성 요소 | 기술 | 목적 |
|----------|------|------|
| Backend | FastAPI | 비동기 API 서버 |
| Frontend | React + TypeScript | 사용자 인터페이스 |
| Database | SQLite | 로컬 데이터 저장소 |
| ASR | Whisper (예정) | 음성-텍스트 변환 |
| Diarization | pyannote.audio (예정) | 화자 분리 |
| Enhancement | DeepFilterNet, WPE (예정) | 음성 정리 |

## 개발 로드맵

| Phase | 초점 | 상태 |
|-------|------|------|
| 1 | 프로젝트 기반 | ✅ 완료 |
| 2 | 음성 파이프라인 & VAD | 🔜 다음 |
| 3 | 한국어 ASR 통합 | 📋 계획됨 |
| 4 | 화자 분리 | 📋 계획됨 |
| 5 | 전사 편집 UI | 📋 계획됨 |
| 6 | 음성 개선 | 📋 계획됨 |
| 7 | 평가 및 지표 | 📋 계획됨 |

## 설계 원칙

### 1. 증거 보존
- 원본 음성 절대 수정 안 함
- 완전한 편집 이력 추적
- 개선 버전 별도 저장

### 2. 투명한 불확실성
- 신뢰도 점수 표시
- AI 예측과 검증된 텍스트 구분
- 낮은 신뢰도 구간 숨기지 않기

### 3. 연구 지향
- 음성 개선 전략 A/B 테스트
- CER/WER 객관적 측정
- 실제 견고성 최적화

## API 엔드포인트 (Phase 1)

### Audio
- `POST /api/audio/upload` - 음성 파일 업로드
- `POST /api/audio/transcribe` - 전사 요청
- `GET /api/audio/file/{file_id}` - 파일 정보 조회

### Projects
- `GET /api/projects/` - 프로젝트 목록
- `POST /api/projects/` - 프로젝트 생성
- `GET /api/projects/{id}` - 프로젝트 상세

### Transcripts
- `GET /api/transcripts/{file_id}/history` - 편집 이력
- `PATCH /api/transcripts/{file_id}` - 전사 수정
- `POST /api/transcripts/{file_id}/export` - 전사 내보내기

전체 API 문서: http://localhost:8003/docs

## 데이터베이스 스키마

### 핵심 테이블
- `audio_files` - 원본 업로드 (불변)
- `processed_audio` - 개선된 음성 변형
- `transcripts` - ASR 결과
- `transcript_segments` - 개별 발화
- `transcript_edits` - 전체 편집 감사 추적
- `evaluations` - 성능 지표

## 개발

상세한 개발 가이드라인은 [CLAUDE.md](./CLAUDE.md)를 참조하세요.

### 주요 명령어

```bash
# 백엔드
cd backend
poetry install                    # 의존성 설치
poetry run uvicorn app.main:app --reload  # 개발 서버 실행
poetry run pytest                 # 테스트 실행

# 프론트엔드
cd frontend
pnpm install                      # 의존성 설치
pnpm dev                          # 개발 서버 실행
pnpm build                        # 프로덕션 빌드
pnpm type-check                   # TypeScript 체크
```

## 기여

이 프로젝트는 단계적 개발 접근 방식을 따릅니다. 현재 초점: **Phase 2** (음성 파이프라인).

## 라이선스

TBD

## 감사의 글

음질을 예측할 수 없는 실제 환경에서 견고한 ASR의 필요성에서 영감을 받았습니다.

---

**참고**: 현재는 Phase 1 - 기반 인프라만 구축되었습니다. AI 모델은 이후 단계에서 통합됩니다.

# 변경 이력 (Changelog)

이 프로젝트의 주요 변경사항을 기록합니다.

**형식:** [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/) 준수
**버전 관리:** [Semantic Versioning](https://semver.org/lang/ko/)

---

## [Unreleased]

### Phase 2 계획
- 파일 업로드 실제 저장
- Silero VAD 통합
- 데이터베이스 초기화 스크립트
- 프론트엔드 업로드 UI

---

## [0.1.0] - 2026-11-16 (Phase 1)

### Added - 새로운 기능
- ✅ Backend API 구조 (FastAPI)
  - `/api/audio/*` - 음성 업로드 및 전사 엔드포인트
  - `/api/projects/*` - 프로젝트 관리
  - `/api/transcripts/*` - 전사 편집 및 내보내기
- ✅ Database 스키마 (SQLite + SQLAlchemy async)
  - 9개 테이블: `audio_files`, `transcripts`, `transcript_segments` 등
  - 원본 보존 설계: `original_text` vs `edited_text` 분리
- ✅ 모델 추상화 레이어
  - `BaseModel` 인터페이스
  - ASR, Diarization, VAD, Enhancement 인터페이스 정의
  - 지연 로딩 및 메모리 관리 지원
- ✅ Frontend 기본 구조 (React + TypeScript)
  - Health status 표시 페이지
  - API 클라이언트 (`services/api.ts`)
  - TypeScript 타입 정의
- ✅ 개발 문서
  - `CLAUDE.md` - 개발 가이드 (한국어)
  - `README.md` - 프로젝트 설명 (한국어)
  - `docs/phase1-completion-report.md` - Phase 1 완료 보고서
  - `docs/DECISIONS.md` - 기술적 결정 기록
  - `docs/CHANGELOG.md` - 이 파일

### Changed - 변경사항
- Backend 포트: 8000 → **8003** (사용자 요청)
  - `vite.config.ts` proxy 설정 업데이트
  - 문서 업데이트
- Poetry 설정: `package-mode = false` 추가
  - README.md 없음 오류 해결

### Technical Decisions - 기술적 결정
- **ADR-001**: FastAPI + React 선택
- **ADR-002**: SQLite + aiosqlite (비동기)
- **ADR-003**: Phase 1에서 AI 모델 미통합 (인터페이스만)
- **ADR-004**: Poetry package-mode = false
- **ADR-005**: Backend 포트 8003 사용

### Testing - 테스트
- ✅ Backend API 엔드포인트 동작 확인
- ✅ 한국어 더미 전사 데이터 반환 확인
- ✅ Frontend-Backend 통신 확인
- ✅ FastAPI 자동 문서 생성 확인 (`/docs`)

### Dependencies - 의존성
**Backend (Python):**
- fastapi ^0.115.0
- uvicorn ^0.32.0
- pydantic ^2.10.0
- sqlalchemy ^2.0.36
- aiosqlite ^0.20.0

**Frontend (Node.js):**
- react ^18.3.1
- vite ^6.0.5
- typescript ~5.6.2

### Files Created - 생성된 파일
- Backend: 21개 파일
- Frontend: 13개 파일
- 문서: 5개 파일 (CLAUDE.md, README.md, 3 docs/*.md)

---

## 변경 이력 작성 가이드

### 카테고리
- **Added**: 새로운 기능
- **Changed**: 기존 기능 변경
- **Deprecated**: 곧 제거될 기능
- **Removed**: 제거된 기능
- **Fixed**: 버그 수정
- **Security**: 보안 관련 변경

### 커밋 메시지 컨벤션
```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 변경
style: 코드 포맷팅 (기능 변경 없음)
refactor: 리팩토링
test: 테스트 추가
chore: 빌드, 설정 변경
```

### 예시
```markdown
## [0.2.0] - 2026-11-XX (Phase 2)

### Added
- 파일 업로드 실제 저장 (`data/uploads/`)
- Silero VAD 통합으로 음성 구간 자동 탐지
- 데이터베이스 자동 초기화 스크립트

### Changed
- `AudioUploadResponse` 스키마에 VAD 결과 추가

### Fixed
- 파일 업로드 크기 제한 (500MB) 적용

### Technical Decisions
- **ADR-006**: Silero VAD 선택 (vs WebRTC VAD)
```

---

**관련 문서:**
- [개발 가이드](../CLAUDE.md)
- [기술적 결정](./DECISIONS.md)
- [Phase 1 보고서](./phase1-completion-report.md)

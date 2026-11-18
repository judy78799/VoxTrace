# VoxTrace 문서 디렉토리

이 디렉토리는 프로젝트 개발 과정의 주요 결정, 변경 이력, Phase별 완료 보고서를 보관합니다.

## 📚 문서 목록

### 핵심 문서
- [`DECISIONS.md`](./DECISIONS.md) - **기술적 결정 기록 (ADR)**
  - 왜 FastAPI를 선택했는가?
  - 왜 SQLite를 사용하는가?
  - 모델 선택 근거는?

- [`CHANGELOG.md`](./CHANGELOG.md) - **변경 이력**
  - Phase별 추가/변경/제거 기능
  - 버전별 의존성 변경
  - 주요 버그 수정 기록

### Phase별 완료 보고서
- [`phase1-completion-report.md`](./phase1-completion-report.md) - **Phase 1: 기반 구축**
  - 생성된 파일 목록
  - 아키텍처 설계
  - 테스트 결과
  - 다음 Phase 제안

- `phase2-completion-report.md` (작성 예정) - **Phase 2: 음성 파이프라인**
- `phase3-completion-report.md` (작성 예정) - **Phase 3: 한국어 ASR**
- ... (향후 추가)

## 📝 문서 작성 규칙

### 1. 기술적 결정 (DECISIONS.md)
**언제 작성:**
- 새로운 라이브러리 도입 시
- 아키텍처 변경 시
- 중요한 설계 선택 시

**템플릿:**
```markdown
## [날짜] ADR-XXX: 결정 제목

**상태:** ✅ 채택됨

**맥락:**
무엇이 문제였는가?

**결정:**
무엇을 선택했는가?

**근거:**
왜 이 선택을 했는가?

**대안:**
고려한 다른 방법은?

**트레이드오프:**
장단점은?
```

### 2. 변경 이력 (CHANGELOG.md)
**언제 작성:**
- 새로운 기능 추가
- 기존 기능 변경
- 버그 수정
- 의존성 업데이트

**카테고리:**
- `Added`: 새 기능
- `Changed`: 변경사항
- `Fixed`: 버그 수정
- `Removed`: 제거된 기능

### 3. Phase 완료 보고서
**언제 작성:**
- 각 Phase 완료 시

**필수 포함 내용:**
- 구현된 기능 목록
- 생성된 파일 및 코드
- 테스트 결과
- 미구현 항목 (의도적)
- 다음 Phase 제안

## 🎯 문서의 목적

### 1. 맥락 보존
- **왜**: 나중에 "왜 이렇게 했지?"라는 질문에 답하기 위해
- **예**: MLX Whisper를 선택한 이유? → DECISIONS.md에 벤치마크 결과 기록

### 2. 온보딩
- 새로운 개발자가 프로젝트를 이해하는 데 필요한 시간 단축
- 설계 의도와 트레이드오프를 명확히 전달

### 3. 회고 및 학습
- Phase별로 무엇을 배웠는가?
- 어떤 결정이 좋았고, 어떤 것이 문제였는가?

### 4. 연구 기록
- "Low-quality Audio Robust Speech Recognition" 연구 과정 문서화
- 실험 결과 및 성능 비교 데이터 보존

## 🔗 관련 문서

**프로젝트 루트:**
- [`../CLAUDE.md`](../CLAUDE.md) - 개발자용 종합 가이드
- [`../README.md`](../README.md) - 사용자용 프로젝트 소개

**외부 참고:**
- [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/)
- [Architecture Decision Records](https://adr.github.io/)
- [Semantic Versioning](https://semver.org/lang/ko/)

## 📌 작성자 가이드

### Phase 완료 시 체크리스트
- [ ] `CHANGELOG.md`에 변경사항 추가
- [ ] 새로운 기술적 결정이 있다면 `DECISIONS.md`에 ADR 작성
- [ ] Phase 완료 보고서 작성 (`phaseN-completion-report.md`)
- [ ] Git 커밋 메시지에 Phase 번호 명시

### 예시 커밋 메시지
```
feat(phase2): Add file upload and VAD integration

- Implemented actual file storage to data/uploads/
- Integrated Silero VAD for voice activity detection
- Added database initialization script

Closes #2
See docs/phase2-completion-report.md for details
```

---

**유지보수:** 매 Phase 완료 시 업데이트
**책임자:** 프로젝트 리드
**검토:** 주요 결정 시 팀 리뷰

# 기술적 결정 기록 (Architecture Decision Records)

이 문서는 VoxTrace 프로젝트에서 내린 중요한 기술적 결정과 그 근거를 기록합니다.

**작성 규칙:**
- 새로운 결정을 내릴 때마다 맨 위에 추가
- 형식: 날짜, 결정 내용, 이유, 대안, 트레이드오프
- 변경된 경우 SUPERSEDED 표시

---

## [2026-11-16] ADR-007: 평가 시스템 설계 (CER 주 지표, 음질별 분류)

**상태:** ✅ 채택됨

**맥락:**
- VoxTrace는 "Low-quality Audio Robust Speech Recognition" 프로젝트
- 단순한 정확도가 아닌 음질별 견고성 측정 필요
- 모델 선택 및 전처리 효과를 객관적으로 비교해야 함

**결정:**
다음과 같은 평가 시스템 구축:
1. **CER을 주 평가 지표**로 사용 (한국어 적합)
2. **음질별 데이터셋 분류** (clean, noisy, reverberant, very_noisy)
3. **Ground Truth 기반 평가** (사람이 검수한 정답 데이터)
4. **실험 조건 관리** (전처리/모델 조합을 DB에 저장)
5. **리소스 사용량 추적** (RTF, Peak RAM, CPU%)

**근거:**

### CER을 주 지표로 선택한 이유
- 한국어는 띄어쓰기 일관성이 낮아 WER이 부정확
- 문자 단위 비교가 더 공정한 평가
- 예: "오늘회의는" vs "오늘 회의는" → WER 100%, CER은 0%

### 음질별 분류의 중요성
- 깨끗한 음성에서 CER 5%보다 잡음 음성에서 CER 15%가 더 의미 있음
- 전처리 효과는 음질별로 다르게 나타남
- 예: 잡음 제거는 noisy에서 효과적, clean에서는 오히려 악화 가능

### Ground Truth 필수성
- AI가 생성한 텍스트를 정답으로 쓰면 circular validation
- 사람이 직접 검수한 정답만 사용

**대안:**

| 방법 | 장점 | 단점 | 결정 |
|------|------|------|------|
| WER 주 지표 | 영어권 표준 | 한국어 띄어쓰기 영향 큼 | ❌ |
| CER 주 지표 | 한국어 적합, 공정 | 의미 단위 무시 | ✅ 채택 |
| 음질 구분 없이 평가 | 단순함 | 저음질 견고성 측정 불가 | ❌ |
| 음질별 데이터셋 | 세밀한 분석 | 데이터 준비 부담 | ✅ 채택 |

**구현:**

```python
# 4개 테이블 추가
- evaluation_datasets: Ground Truth 관리
- experiment_configs: 실험 조건
- evaluations: 평가 결과 (확장됨)
- model_benchmarks: 모델별 종합 성능

# 평가 코드
- app/evaluation/metrics.py: CER/WER 계산 (jiwer)
- app/evaluation/benchmark.py: 벤치마크 실행, 리소스 모니터링
```

**트레이드오프:**
- 장점: 객관적 성능 비교, 음질별 견고성 측정, 재현 가능한 실험
- 단점: Ground Truth 준비 시간 필요, DB 스키마 복잡도 증가

**의존성 추가:**
- `jiwer`: CER/WER 계산
- `psutil`: 리소스 모니터링 (이미 Python 표준)

**측정 지표:**

| 지표 | 설명 | 목표 |
|------|------|------|
| CER | Character Error Rate | < 15% (noisy 기준) |
| WER | Word Error Rate | 참고용 |
| DER | Diarization Error Rate | Phase 4+ |
| RTF | Real-Time Factor | < 1.0 (실시간보다 빠름) |
| Peak RAM | 최대 메모리 | < 8GB (M4 16GB 절반) |

**다음 단계:**
- Phase 3: ASR 모델 벤치마크 (MLX Whisper vs faster-whisper)
- Phase 6: 전처리 효과 A/B 테스트

---

## [2026-11-16] ADR-006: Poetry 가상환경을 프로젝트 내부(.venv)로 변경

**상태:** ⏳ 제안됨 (사용자 결정 대기)

**맥락:**
- Poetry 기본 설정은 캐시 디렉토리에 가상환경 생성
- 사용자가 Poetry를 처음 사용
- IDE 자동 인식 및 명확한 경로가 필요할 수 있음

**결정 (제안):**
`poetry config virtualenvs.in-project true` 설정으로 `backend/.venv`에 가상환경 생성

**근거:**
1. **IDE 자동 인식**: VSCode/PyCharm이 `.venv` 자동 감지
2. **명확한 경로**: 프로젝트 폴더 내 위치
3. **전통적 워크플로우**: `source .venv/bin/activate` 사용 가능
4. **디버깅 편의성**: 인터프리터 경로 명확

**대안:**

| 방법 | 경로 | 장점 | 단점 |
|------|------|------|------|
| 기본 (캐시) | `~/Library/Caches/pypoetry/...` | 프로젝트 폴더 깨끗, 공간 절약 | IDE 인식 어려움 |
| 프로젝트 내부 | `backend/.venv` | IDE 자동 인식, 경로 명확 | 폴더 용량 증가 (~200MB) |

**트레이드오프:**
- 장점: VSCode에서 Python 인터프리터 자동 감지, `activate` 스크립트 직접 사용
- 단점: `.gitignore`에 `.venv` 추가 필요, 디스크 용량 약간 증가

**변경 시 영향:**
- `.gitignore`에 `backend/.venv/` 추가
- CLAUDE.md에 설정 방법 문서화
- VSCode `.vscode/settings.json` 생성 가능

**변경 명령어:**
```bash
cd backend
poetry config virtualenvs.in-project true
poetry env remove python3.11  # 기존 가상환경 삭제
poetry install                 # .venv에 재생성
```

---

## [2026-11-16] ADR-005: Backend 포트 8003 사용

**상태:** ✅ 채택됨

**맥락:**
- 기본 설계는 8000 포트 사용 예정
- 사용자 환경에서 8000 포트 충돌 발생

**결정:**
Backend 포트를 8003으로 변경

**근거:**
- 사용자 요청
- 포트 충돌 회피
- 프론트엔드 프록시 설정 간단히 변경 가능

**영향받는 파일:**
- `backend/app/core/config.py` (설정은 없지만 문서화)
- `frontend/vite.config.ts:10` (proxy target)
- `README.md` (문서)

**트레이드오프:**
- 표준 포트(8000)에서 벗어남
- 하지만 로컬 개발 환경이므로 문제없음

---

## [2026-11-16] ADR-004: Poetry package-mode = false 설정

**상태:** ✅ 채택됨

**문제:**
```
Error: Readme path `/Users/judy/Desktop/github/VoxTrace/backend/README.md` does not exist.
```

**결정:**
`pyproject.toml`에 `package-mode = false` 추가

**근거:**
- VoxTrace는 배포용 라이브러리가 아닌 애플리케이션
- Poetry 기본 동작은 패키지 빌드를 가정
- `--no-root` 플래그 대신 설정으로 해결

**대안:**
1. `backend/README.md` 생성 (불필요한 중복)
2. 매번 `poetry install --no-root` 실행 (번거로움)
3. `package-mode = false` 설정 (채택)

**참고:**
- Poetry 1.2.0+ 지원
- `packages` 설정 불필요

---

## [2026-11-16] ADR-003: 모델 인터페이스 우선 구현 (Phase 1)

**상태:** ✅ 채택됨

**맥락:**
- M4 Mac 16GB 메모리 환경
- Whisper 모델 선택 불확실 (MLX vs faster-whisper)
- 전체 아키텍처 검증 필요

**결정:**
Phase 1에서 실제 AI 모델을 통합하지 않고, 인터페이스만 정의하고 더미 응답 구현

**근거:**
1. **벤치마크 필요성**: MLX Whisper와 faster-whisper의 M4 성능 비교 필요
2. **아키텍처 검증**: 모델 없이도 API 흐름 테스트 가능
3. **메모리 관리**: 점진적 통합으로 메모리 사용량 최적화
4. **병렬 개발**: 프론트엔드 개발을 모델 통합과 독립적으로 진행

**구현:**
```python
# backend/app/models/base.py
class BaseModel(ABC):
    async def load(self) -> None: ...
    async def unload(self) -> None: ...
    def get_info(self) -> ModelInfo: ...
```

**효과:**
- ✅ API 엔드포인트 테스트 가능
- ✅ 프론트엔드 개발 병렬 진행
- ✅ 데이터베이스 스키마 검증

**향후 계획:**
- Phase 3: 실제 ASR 모델 벤치마크 및 통합

---

## [2026-11-16] ADR-002: SQLite + 비동기 (aiosqlite) 선택

**상태:** ✅ 채택됨

**맥락:**
- 로컬 우선 애플리케이션
- 긴 ASR 작업 시 UI 블로킹 방지 필요

**결정:**
SQLite + SQLAlchemy async + aiosqlite 사용

**대안 비교:**

| 방안 | 장점 | 단점 | 결정 |
|------|------|------|------|
| SQLite 동기 | 단순함 | 블로킹, 확장성 제한 | ❌ |
| SQLite 비동기 | 비블로킹, FastAPI 일관성 | 복잡도 증가 | ✅ 채택 |
| PostgreSQL | 기능 풍부, 동시성 우수 | 설치 필요, 과한 스펙 | ❌ |

**근거:**
1. **로컬 우선**: 별도 DB 서버 불필요
2. **비동기 패턴**: FastAPI와 일관성, ASR 작업 중 다른 요청 처리 가능
3. **단순 배포**: 단일 파일 DB, 백업 간편
4. **충분한 성능**: 단일 사용자 환경에서는 SQLite로 충분

**트레이드오프:**
- 복잡도 약간 증가 (async/await)
- 하지만 확장성과 UX 개선 효과가 더 큼

**벤치마크 필요성:**
- Phase 3+에서 긴 전사 작업 시 실제 응답성 측정

---

## [2026-11-16] ADR-001: FastAPI + React 선택

**상태:** ✅ 채택됨

**맥락:**
- 로컬 우선 음성 인식 시스템
- Python AI 생태계 활용 필요
- 사용자 친화적 UI 필요

**결정:**
- Backend: FastAPI (Python)
- Frontend: React + TypeScript + Vite

**근거:**

### Backend: FastAPI 선택 이유
1. **Python 생태계**: Whisper, pyannote, librosa 등 모든 AI 라이브러리가 Python 우선
2. **비동기 지원**: 긴 ASR 작업 중 UI 블로킹 방지
3. **자동 문서화**: `/docs` 엔드포인트로 API 스펙 자동 생성
4. **타입 힌트**: Pydantic으로 요청/응답 검증

**대안:**
- Flask: 비동기 지원 약함
- Django: 과한 기능 (ORM, Admin 등 불필요)
- Node.js: Python AI 라이브러리 사용 어려움

### Frontend: React 선택 이유
1. **컴포넌트 재사용**: 전사 편집기, 오디오 플레이어 등 복잡한 UI
2. **생태계**: 음성 시각화 라이브러리 풍부
3. **TypeScript**: 백엔드 API 타입과 동기화 가능

**대안:**
- Vue: 러닝 커브는 낮지만 생태계 작음
- Svelte: 가볍지만 음성 처리 라이브러리 적음
- Pure HTML: 복잡한 편집 UI 구현 어려움

**트레이드오프:**
- React 번들 크기 큼 → 하지만 로컬 앱이므로 무관
- TypeScript 러닝 커브 → 타입 안전성으로 상쇄

---

## 템플릿 (복사해서 사용)

```markdown
## [YYYY-MM-DD] ADR-XXX: 결정 제목

**상태:** ✅ 채택됨 / ⏳ 제안됨 / ❌ 기각됨 / 🔄 변경됨

**맥락:**
무엇이 문제였는가?

**결정:**
무엇을 선택했는가?

**근거:**
왜 이 선택을 했는가?

**대안:**
다른 선택지는 무엇이었는가?

**트레이드오프:**
이 결정의 장단점은?

**영향:**
어떤 파일/시스템이 영향을 받는가?
```

---

**관련 문서:**
- [Phase 완료 보고서](./phase1-completion-report.md)
- [변경 이력](./CHANGELOG.md)

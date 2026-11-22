# VoxTrace 커밋 컨벤션

## 커밋 메시지 형식

```
<type>(<scope>): <subject>

<body>
```

## Type (필수)

| Type | 설명 | 예시 |
|------|------|------|
| `feat` | 새로운 기능 추가 | feat(asr): MLX Whisper 모델 통합 |
| `fix` | 버그 수정 | fix(vad): 무음 구간 감지 오류 수정 |
| `docs` | 문서 변경 | docs: Phase 1 완료 보고서 추가 |
| `style` | UI/UX 개선 (코드 동작 변경 없음) | style(frontend): 스펙트로그램 레이아웃 개선 |
| `refactor` | 코드 리팩토링 | refactor(api): 오디오 처리 파이프라인 재구성 |
| `perf` | 성능 개선 | perf(asr): 메모리 사용량 50% 감소 |
| `test` | 테스트 추가/수정 | test(asr): Mozilla Common Voice 테스트 추가 |
| `chore` | 빌드, 의존성, 설정 변경 | chore(deps): numpy 1.24.0으로 업데이트 |
| `build` | 빌드 시스템 변경 | build: Docker 환경 설정 추가 |

## Scope (선택)

프로젝트 영역을 나타냅니다:

| Scope | 설명 |
|-------|------|
| `backend` | 백엔드 전반 |
| `frontend` | 프론트엔드 전반 |
| `asr` | 음성 인식 모델 |
| `vad` | Voice Activity Detection |
| `enhancement` | 음성 개선 |
| `diarization` | 화자 분리 |
| `api` | REST API 엔드포인트 |
| `db` | 데이터베이스 스키마/쿼리 |
| `ui` | 사용자 인터페이스 |
| `config` | 설정 파일 |
| `deps` | 의존성 패키지 |

## Subject (필수)

- 50자 이내로 간결하게 작성
- 명령형 현재 시제 사용 ("추가함" ❌, "추가" ✅)
- 첫 글자 소문자
- 마침표 없음
- 무엇을 왜 했는지 명확히

## Body (선택)

- 72자마다 줄바꿈
- 무엇을, 왜 변경했는지 설명
- 어떻게 변경했는지는 코드에서 확인 가능하므로 생략 가능

## 예시

### 1. 기능 추가
```
feat(asr): MLX Whisper medium 모델 통합

- M4 Mac에서 최적화된 추론 속도
- 한국어 CER 12.3% 달성
- 메모리 사용량 2.1GB
```

### 2. 버그 수정
```
fix(vad): Silero VAD 무음 구간 과도 제거 문제 해결

임계값을 0.3에서 0.5로 조정하여 짧은 발화가
잘리는 문제 수정
```

### 3. UI 개선
```
style(frontend): 스펙트로그램 전체 너비로 표시

작은 카드에서 분리하여 별도 섹션으로 배치
시각적 분석 편의성 향상
```

### 4. 문서 작성
```
docs: Phase 1 완료 보고서 추가

- 구현된 기능 목록
- 데이터베이스 스키마
- API 엔드포인트 명세
```

### 5. 리팩토링
```
refactor(api): 오디오 처리 파이프라인 재구성

Enhancement → VAD → ASR 순서로 명확히 분리
각 단계별 에러 핸들링 개선
```

## Breaking Changes

호환성이 깨지는 변경사항은 커밋 메시지에 `BREAKING CHANGE:` 추가:

```
feat(api)!: 전사 API 응답 형식 변경

BREAKING CHANGE: TranscriptionResult 스키마에서
segments 필드 구조 변경. 기존 클라이언트는
API 버전 업데이트 필요.
```

## 커밋 크기

- 1개의 논리적 변경사항 = 1개의 커밋
- 너무 큰 커밋은 여러 개로 분리
- 관련 없는 변경사항은 별도 커밋

## 참고

이 컨벤션은 [Conventional Commits](https://www.conventionalcommits.org/)를 기반으로 VoxTrace 프로젝트에 맞게 조정되었습니다.

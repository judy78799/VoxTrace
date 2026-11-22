# Changelog

VoxTrace 프로젝트의 모든 중요한 변경사항은 이 문서에 기록됩니다.

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/)를 따르며,
버전 관리는 [Semantic Versioning](https://semver.org/lang/ko/)을 준수합니다.

---

## [Unreleased]

### 2026-11-22

#### Added
- **DeepFilterNet 음성 향상 모델 통합** (`backend/app/models/enhancement.py`)
  - 딥러닝 기반 고품질 노이즈 제거 (v0.5.6)
  - 두 가지 방법 지원: `deepfilternet` (기본), `noisereduce` (빠른 처리)
  - 자동 fallback: DeepFilterNet 실패 시 noisereduce 사용
  - 48kHz 처리 최적화, CPU 실시간 처리 가능
  - 복잡한 소음 환경에서 ASR 정확도 대폭 향상

- **스펙트로그램 UI 개선** (`frontend/src/components/AudioUpload.tsx`)
  - 전체 너비로 표시하여 가독성 향상
  - 작은 카드에서 분리하여 별도 섹션 배치
  - 시각적 분석 편의성 대폭 개선

- **오디오 품질 분석 및 세그먼트 필터링**
  - 신호 분석 결과를 전사 API 응답에 통합
  - 품질 플래그 및 의심 세그먼트 자동 필터링
  - 반복 패턴, 짧은 텍스트, 낮은 신뢰도 자동 감지
  - 세그먼트별 품질 플래그 시각화 (경고/오류 색상)
  - 필터링된 세그먼트 숨김/표시 토글 기능

- **실시간 전사 진행 상황 표시 - 아코디언 스타일** (SSE)
  - Server-Sent Events 기반 실시간 진행 업데이트
  - 8단계 파이프라인 단계별 시각화 (로딩 → 분석 → Enhancement → VAD → ASR → 저장 → 후처리 → 완료)
  - 각 메인 단계별 세부 작업 목록 표시 (예: FFT 변환, SNR 계산, Whisper 모델 로딩 등)
  - 아코디언 스타일: 진행 중인 단계는 펼쳐지고, 완료된 단계는 접혀서 작게 표시
  - 세부 작업 상태 추적: 완료(✓), 진행중(⏳), 대기(회색)
  - 완료된 세부 작업은 취소선 처리되어 사라지는 효과
  - 각 단계별 진행률(0-100%) 및 이모지 아이콘 표시
  - Backend: 각 단계당 4-7개의 substep 이벤트 emit
  - Frontend: 동적 substep 추적 및 아코디언 애니메이션

- **커밋 컨벤션 가이드** (`COMMIT_CONVENTION.md`)
  - Conventional Commits 기반
  - VoxTrace 프로젝트 특화 scope 정의
  - 실용적인 예시 포함

#### Changed
- **.gitignore 개선**
  - 기존: `models/` 전체 무시 → AI 모델 파일과 Python 코드 모두 무시
  - 개선: AI 모델 파일(`*.pt`, `*.pth` 등)만 무시, Python 코드는 추적
  - 이전에 무시되던 모델 코드 파일들 git에 추가

- **EnhancementResult 스키마 확장**
  - `method` 필드 추가: 사용된 enhancement 방법 추적
  - `"deepfilternet"` 또는 `"noisereduce"` 값 반환

#### Fixed
- **데이터베이스 초기화 로그 메시지 명확화**
  - "초기화 완료" → "준비 완료 (기존 데이터 보존됨)"
  - SQLAlchemy의 `create_all()`이 기존 데이터를 삭제하지 않음을 명시
  - 사용자 오해 방지

---

## 이전 변경사항

### 2026-11-21

#### Added
- **오디오 신호 분석 모듈** (`backend/app/models/audio_analysis.py`)
  - SNR (Signal-to-Noise Ratio) 계산
  - Mel Spectrogram 생성 (Base64 PNG)
  - 주파수 분석 (저/중/고 대역별 에너지)
  - 클리핑 감지
  - 품질 점수 자동 평가 (0-100)

- **Mozilla Common Voice 테스트**
  - 한국어 ASR 테스트 스크립트
  - 테스트 결과 보고서 자동 생성
  - CER/WER 계산

#### Fixed
- Settings에 `MOZILLA_API_KEY` 필드 추가

---

## 버전 관리 가이드

### 버전 번호 체계: MAJOR.MINOR.PATCH

- **MAJOR**: 호환되지 않는 API 변경
- **MINOR**: 하위 호환되는 기능 추가
- **PATCH**: 하위 호환되는 버그 수정

### 변경사항 분류

- **Added**: 새로운 기능
- **Changed**: 기존 기능 변경
- **Deprecated**: 곧 제거될 기능
- **Removed**: 제거된 기능
- **Fixed**: 버그 수정
- **Security**: 보안 취약점 수정

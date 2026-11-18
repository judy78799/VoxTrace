"""
Evaluation Metrics

CER, WER, DER 계산 유틸리티
"""

from typing import Dict, List, Tuple, Optional
import re


def normalize_korean_text(text: str) -> str:
    """
    한국어 텍스트 정규화

    - 공백 제거 (CER 계산용)
    - 소문자 변환
    - 특수문자 정리
    """
    # 앞뒤 공백 제거
    text = text.strip()

    # 연속된 공백을 하나로
    text = re.sub(r'\s+', ' ', text)

    return text


def calculate_cer(reference: str, hypothesis: str) -> Dict[str, float]:
    """
    Character Error Rate (CER) 계산

    한국어 음성 인식 평가의 주 지표

    Args:
        reference: 정답 텍스트 (Ground Truth)
        hypothesis: 모델 예측 텍스트

    Returns:
        {
            "cer": 0.125,           # Character Error Rate
            "substitutions": 5,      # 치환 오류 수
            "deletions": 2,          # 삭제 오류 수
            "insertions": 1,         # 삽입 오류 수
            "total_chars": 64        # 총 문자 수
        }
    """
    try:
        import jiwer
    except ImportError:
        raise ImportError(
            "jiwer 패키지가 필요합니다. 'poetry add jiwer' 또는 'pip install jiwer' 실행"
        )

    # 공백 포함 문자 단위 계산 (한국어 CER)
    ref_normalized = normalize_korean_text(reference)
    hyp_normalized = normalize_korean_text(hypothesis)

    # jiwer로 문자 단위 계산
    # CER = (S + D + I) / N
    # S: Substitutions, D: Deletions, I: Insertions, N: Reference length
    measures = jiwer.compute_measures(
        ref_normalized,
        hyp_normalized,
    )

    return {
        "cer": measures["wer"],  # jiwer의 wer이 사실상 CER (character 단위로 적용)
        "substitutions": measures["substitutions"],
        "deletions": measures["deletions"],
        "insertions": measures["insertions"],
        "total_chars": len(ref_normalized),
    }


def calculate_wer(reference: str, hypothesis: str) -> Dict[str, float]:
    """
    Word Error Rate (WER) 계산

    보조 지표 (한국어는 띄어쓰기 불일치로 부정확할 수 있음)

    Args:
        reference: 정답 텍스트
        hypothesis: 모델 예측 텍스트

    Returns:
        {
            "wer": 0.25,
            "substitutions": 3,
            "deletions": 1,
            "insertions": 0,
            "total_words": 16
        }
    """
    try:
        import jiwer
    except ImportError:
        raise ImportError("jiwer 패키지가 필요합니다.")

    ref_normalized = normalize_korean_text(reference)
    hyp_normalized = normalize_korean_text(hypothesis)

    # 어절 단위로 분리
    ref_words = ref_normalized.split()
    hyp_words = hyp_normalized.split()

    measures = jiwer.compute_measures(
        " ".join(ref_words),
        " ".join(hyp_words),
    )

    return {
        "wer": measures["wer"],
        "substitutions": measures["substitutions"],
        "deletions": measures["deletions"],
        "insertions": measures["insertions"],
        "total_words": len(ref_words),
    }


def calculate_der(
    reference_segments: List[Dict],
    hypothesis_segments: List[Dict],
    collar: float = 0.25,
) -> Dict[str, float]:
    """
    Diarization Error Rate (DER) 계산

    화자 분리 평가 지표

    Args:
        reference_segments: 정답 화자 분리
            [{"start": 0.0, "end": 3.5, "speaker": "A"}, ...]
        hypothesis_segments: 모델 예측 화자 분리
            [{"start": 0.0, "end": 3.2, "speaker": "SPEAKER_00"}, ...]
        collar: 허용 오차 (초 단위, 기본 0.25초)

    Returns:
        {
            "der": 0.18,              # Diarization Error Rate
            "miss_rate": 0.05,        # Missed Speech
            "false_alarm_rate": 0.03, # False Alarm
            "confusion_rate": 0.10,   # Speaker Confusion
        }

    Note:
        실제 DER 계산은 pyannote.metrics 등 전문 라이브러리 사용 권장
        Phase 4에서 구현 예정
    """
    # Phase 4에서 pyannote.metrics로 구현
    # 현재는 인터페이스만 정의
    raise NotImplementedError(
        "DER 계산은 Phase 4(화자 분리)에서 구현 예정. "
        "pyannote.metrics 라이브러리 사용 계획"
    )


def calculate_rtf(processing_time: float, audio_duration: float) -> float:
    """
    Real-Time Factor (RTF) 계산

    RTF = Processing Time / Audio Duration

    Args:
        processing_time: 모델 처리 시간 (초)
        audio_duration: 음성 파일 길이 (초)

    Returns:
        RTF 값
        - < 1.0: 실시간보다 빠름
        - = 1.0: 실시간과 동일
        - > 1.0: 실시간보다 느림

    Example:
        >>> calculate_rtf(15.0, 60.0)  # 60초 음성을 15초만에 처리
        0.25
    """
    if audio_duration == 0:
        return float('inf')

    return processing_time / audio_duration


def compare_evaluations(
    baseline: Dict[str, float],
    experiment: Dict[str, float],
) -> Dict[str, Dict[str, float]]:
    """
    두 평가 결과 비교

    Args:
        baseline: 기준 평가 (예: 원본 음성)
        experiment: 비교 평가 (예: 전처리 음성)

    Returns:
        {
            "cer": {"baseline": 15.2, "experiment": 12.5, "improvement": 2.7},
            "wer": {"baseline": 22.1, "experiment": 18.3, "improvement": 3.8},
            ...
        }
    """
    result = {}

    for metric in baseline.keys():
        if metric in experiment:
            base_val = baseline[metric]
            exp_val = experiment[metric]

            # 낮을수록 좋은 지표 (cer, wer, der)는 improvement가 양수
            improvement = base_val - exp_val

            result[metric] = {
                "baseline": base_val,
                "experiment": exp_val,
                "improvement": improvement,
                "improvement_percent": (improvement / base_val * 100) if base_val > 0 else 0.0,
            }

    return result

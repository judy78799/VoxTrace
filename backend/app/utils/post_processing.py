"""
Post-processing filters for transcription quality analysis

Detects suspicious segments that may be noise/artifacts even with high confidence scores
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class QualityFlag:
    """Quality flag for a segment"""
    flag_type: str  # "repetition", "character_repetition", "suspicious", "low_confidence"
    severity: str   # "warning", "error"
    reason: str     # Human-readable explanation


def detect_character_repetition(text: str, min_repeats: int = 3) -> Optional[QualityFlag]:
    """
    Detect character/syllable repetition (e.g., "아아아아")

    Args:
        text: Text to analyze
        min_repeats: Minimum number of repetitions to flag

    Returns:
        QualityFlag if repetition detected, None otherwise
    """
    # Remove whitespace for analysis
    clean_text = text.replace(" ", "")

    if len(clean_text) < min_repeats:
        return None

    # Check for single character repetition
    for i in range(len(clean_text) - min_repeats + 1):
        char = clean_text[i]
        # Count consecutive occurrences
        count = 1
        for j in range(i + 1, len(clean_text)):
            if clean_text[j] == char:
                count += 1
            else:
                break

        if count >= min_repeats:
            # Calculate repetition ratio
            repetition_ratio = count / len(clean_text)

            if repetition_ratio > 0.5:  # More than 50% is same character
                return QualityFlag(
                    flag_type="character_repetition",
                    severity="error",
                    reason=f"단일 문자 반복 감지: '{char}' x {count} (전체 텍스트의 {repetition_ratio*100:.0f}%)"
                )

    # Check for 2-character pattern repetition (e.g., "아아" repeated)
    for pattern_len in [2, 3]:
        for i in range(len(clean_text) - pattern_len * min_repeats + 1):
            pattern = clean_text[i:i+pattern_len]
            # Count how many times this pattern repeats consecutively
            count = 1
            pos = i + pattern_len
            while pos + pattern_len <= len(clean_text):
                if clean_text[pos:pos+pattern_len] == pattern:
                    count += 1
                    pos += pattern_len
                else:
                    break

            if count >= min_repeats:
                repetition_ratio = (count * pattern_len) / len(clean_text)
                if repetition_ratio > 0.4:
                    return QualityFlag(
                        flag_type="character_repetition",
                        severity="error",
                        reason=f"패턴 반복 감지: '{pattern}' x {count}"
                    )

    return None


def detect_word_repetition(text: str, min_repeats: int = 2) -> Optional[QualityFlag]:
    """
    Detect word/phrase repetition (e.g., "지금 이 사람은 지금 이 사람은")

    Args:
        text: Text to analyze
        min_repeats: Minimum number of word repetitions to flag

    Returns:
        QualityFlag if repetition detected, None otherwise
    """
    # Split into words
    words = text.split()

    if len(words) < min_repeats * 2:  # Need at least 2 words repeated twice
        return None

    # Check for consecutive word sequences
    for seq_len in range(len(words) // min_repeats, 0, -1):  # From longest to shortest
        for i in range(len(words) - seq_len * min_repeats + 1):
            sequence = words[i:i+seq_len]

            # Count consecutive repetitions
            count = 1
            pos = i + seq_len
            while pos + seq_len <= len(words):
                if words[pos:pos+seq_len] == sequence:
                    count += 1
                    pos += seq_len
                else:
                    break

            if count >= min_repeats:
                sequence_text = " ".join(sequence)
                repetition_ratio = (count * seq_len) / len(words)

                if repetition_ratio > 0.4:  # More than 40% of text is repetition
                    return QualityFlag(
                        flag_type="word_repetition",
                        severity="error",
                        reason=f"단어/구문 반복 감지: '{sequence_text}' x {count}"
                    )

    return None


def detect_low_linguistic_variety(text: str) -> Optional[QualityFlag]:
    """
    Detect segments with very low linguistic variety (might be noise)

    Args:
        text: Text to analyze

    Returns:
        QualityFlag if low variety detected, None otherwise
    """
    if len(text.strip()) < 5:
        return None

    # Count unique characters (excluding spaces)
    chars = [c for c in text if c.strip()]
    unique_chars = set(chars)

    if len(chars) >= 10 and len(unique_chars) <= 3:
        return QualityFlag(
            flag_type="low_variety",
            severity="warning",
            reason=f"언어적 다양성 부족: {len(chars)}개 문자 중 {len(unique_chars)}개 고유 문자만 사용"
        )

    return None


def detect_suspicious_confidence_mismatch(
    text: str,
    confidence: float,
    duration: float
) -> Optional[QualityFlag]:
    """
    Detect suspiciously high confidence for potentially problematic segments

    Args:
        text: Text content
        confidence: Confidence score (0-1)
        duration: Segment duration in seconds

    Returns:
        QualityFlag if suspicious, None otherwise
    """
    # Very short segment with very high confidence might be suspicious
    if duration < 0.5 and confidence > 0.9 and len(text.strip()) < 5:
        return QualityFlag(
            flag_type="suspicious_confidence",
            severity="warning",
            reason=f"짧은 세그먼트({duration:.1f}s)에 과도한 신뢰도({confidence*100:.0f}%)"
        )

    # Long segment with single word/character repeated
    if duration > 3.0 and len(text.split()) <= 2:
        return QualityFlag(
            flag_type="suspicious_length",
            severity="warning",
            reason=f"긴 세그먼트({duration:.1f}s)에 과도하게 짧은 텍스트"
        )

    return None


def analyze_segment_quality(
    text: str,
    confidence: float,
    start_time: float,
    end_time: float,
) -> Tuple[List[QualityFlag], bool]:
    """
    Analyze segment quality and return all detected issues

    Args:
        text: Segment text
        confidence: Confidence score (0-1)
        start_time: Segment start time
        end_time: Segment end time

    Returns:
        Tuple of (list of quality flags, is_suspicious boolean)
    """
    flags = []
    duration = end_time - start_time

    # Run all detection algorithms
    checks = [
        detect_character_repetition(text),
        detect_word_repetition(text),
        detect_low_linguistic_variety(text),
        detect_suspicious_confidence_mismatch(text, confidence, duration),
    ]

    # Collect all non-None flags
    for flag in checks:
        if flag is not None:
            flags.append(flag)

    # Determine if segment is suspicious (has any error-level flags)
    is_suspicious = any(flag.severity == "error" for flag in flags)

    # Also flag as suspicious if confidence is genuinely low
    if confidence < 0.5 and len(flags) == 0:
        flags.append(QualityFlag(
            flag_type="low_confidence",
            severity="warning",
            reason=f"낮은 신뢰도 ({confidence*100:.0f}%)"
        ))

    return flags, is_suspicious


def filter_suspicious_segments(
    segments: List[dict],
    auto_filter: bool = False
) -> List[dict]:
    """
    Filter segments based on quality flags

    Args:
        segments: List of segment dictionaries with text, confidence, start, end
        auto_filter: If True, mark suspicious segments as filtered

    Returns:
        List of segments with quality_flags and is_filtered fields added
    """
    processed_segments = []

    for seg in segments:
        # Analyze quality
        flags, is_suspicious = analyze_segment_quality(
            text=seg.get("text", ""),
            confidence=seg.get("confidence", 1.0),
            start_time=seg.get("start", 0.0),
            end_time=seg.get("end", 0.0),
        )

        # Add quality information to segment
        processed_seg = seg.copy()
        processed_seg["quality_flags"] = [
            {
                "type": flag.flag_type,
                "severity": flag.severity,
                "reason": flag.reason,
            }
            for flag in flags
        ]
        processed_seg["is_suspicious"] = is_suspicious
        processed_seg["is_filtered"] = auto_filter and is_suspicious

        processed_segments.append(processed_seg)

    return processed_segments

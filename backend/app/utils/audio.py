"""
Audio Processing Utilities

오디오 파일 메타데이터 추출 및 처리 유틸리티
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Optional


def extract_metadata_ffmpeg(file_path: str) -> Dict[str, any]:
    """
    FFmpeg를 사용하여 오디오 메타데이터 추출

    Args:
        file_path: 오디오 파일 경로

    Returns:
        {
            "duration": 120.5,      # 초
            "sample_rate": 16000,   # Hz
            "channels": 1,          # mono/stereo
            "format": "wav",        # 파일 포맷
            "bit_rate": 256000,     # bits/sec (optional)
        }

    Raises:
        FileNotFoundError: 파일이 존재하지 않음
        RuntimeError: FFmpeg 실행 실패
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    # FFprobe로 메타데이터 추출
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFprobe failed: {e.stderr}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse FFprobe output: {e}")

    # 오디오 스트림 찾기
    audio_stream = None
    for stream in data.get('streams', []):
        if stream.get('codec_type') == 'audio':
            audio_stream = stream
            break

    if not audio_stream:
        raise RuntimeError("No audio stream found in file")

    # 메타데이터 추출
    format_info = data.get('format', {})

    return {
        "duration": float(format_info.get('duration', 0)),
        "sample_rate": int(audio_stream.get('sample_rate', 0)),
        "channels": int(audio_stream.get('channels', 0)),
        "format": file_path.suffix.lstrip('.').lower(),
        "bit_rate": int(audio_stream.get('bit_rate', 0)) if audio_stream.get('bit_rate') else None,
        "codec": audio_stream.get('codec_name', 'unknown'),
    }


def validate_audio_file(file_path: str, max_duration: Optional[float] = None) -> bool:
    """
    오디오 파일 유효성 검사

    Args:
        file_path: 오디오 파일 경로
        max_duration: 최대 허용 길이 (초), None이면 무제한

    Returns:
        유효하면 True

    Raises:
        ValueError: 파일이 유효하지 않음
    """
    try:
        metadata = extract_metadata_ffmpeg(file_path)
    except (FileNotFoundError, RuntimeError) as e:
        raise ValueError(f"Invalid audio file: {e}")

    # 길이 검사
    if max_duration and metadata['duration'] > max_duration:
        raise ValueError(
            f"Audio too long: {metadata['duration']:.1f}s "
            f"(max: {max_duration:.1f}s)"
        )

    # 샘플레이트 검사 (일반적인 범위)
    if not (8000 <= metadata['sample_rate'] <= 192000):
        raise ValueError(f"Invalid sample rate: {metadata['sample_rate']} Hz")

    # 채널 검사
    if metadata['channels'] < 1 or metadata['channels'] > 8:
        raise ValueError(f"Invalid channel count: {metadata['channels']}")

    return True

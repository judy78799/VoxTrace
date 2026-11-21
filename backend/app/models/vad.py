"""
VAD (Voice Activity Detection) Model Interface

Silero VAD를 사용하여 오디오에서 음성 구간만 추출
무음 구간 제거로 ASR 처리 시간 단축
"""

import time
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

import torch
import torchaudio
from silero_vad import load_silero_vad, get_speech_timestamps, collect_chunks

from app.models.base import BaseModel, ModelInfo


@dataclass
class VADSegment:
    """음성 구간 정보"""
    start: float  # 시작 시간 (초)
    end: float    # 종료 시간 (초)


@dataclass
class VADResult:
    """VAD 처리 결과"""
    segments: List[VADSegment]  # 음성 구간 목록
    original_duration: float     # 원본 길이 (초)
    processed_duration: float    # 처리 후 길이 (초)
    silence_removed: float       # 제거된 무음 길이 (초)
    processing_time: float       # 처리 시간 (초)


class VADModel(BaseModel):
    """
    Silero VAD 기반 음성 구간 감지

    무음 구간을 제거하여 ASR 처리 시간을 단축시킵니다
    """

    def __init__(self):
        super().__init__()
        self._model = None
        self._sample_rate = 16000  # Silero VAD 권장 샘플레이트

    async def load(self) -> None:
        """Silero VAD 모델 로딩"""
        if self._loaded:
            return

        print("🔄 Loading Silero VAD model...")

        try:
            # Silero VAD 모델 로드
            self._model = load_silero_vad()
            self._loaded = True

            print("✅ Silero VAD loaded successfully")
            print(f"   Sample rate: {self._sample_rate} Hz")

        except Exception as e:
            print(f"❌ Failed to load VAD model: {e}")
            raise

    async def unload(self) -> None:
        """메모리에서 모델 언로드"""
        if self._loaded:
            self._model = None
            self._loaded = False
            print("🗑️  Silero VAD unloaded")

    async def process_audio(
        self,
        audio_path: str,
        output_path: Optional[str] = None,
        threshold: float = 0.5,
        min_speech_duration_ms: int = 250,
        min_silence_duration_ms: int = 100,
    ) -> VADResult:
        """
        오디오 파일에서 음성 구간만 추출

        Args:
            audio_path: 입력 오디오 파일 경로
            output_path: 출력 파일 경로 (None이면 자동 생성)
            threshold: VAD 임계값 (0.0-1.0, 높을수록 엄격)
            min_speech_duration_ms: 최소 음성 길이 (밀리초)
            min_silence_duration_ms: 최소 무음 길이 (밀리초)

        Returns:
            VADResult with segments and processing info
        """
        if not self._loaded:
            await self.load()

        start_time = time.time()

        # 디버그 로깅
        print(f"\n{'='*60}")
        print(f"🎙️  VAD Processing Started")
        print(f"{'='*60}")
        print(f"📁 Audio Path: {audio_path}")
        print(f"🎚️  Threshold: {threshold}")
        print(f"⏱️  Min Speech Duration: {min_speech_duration_ms}ms")
        print(f"🔇 Min Silence Duration: {min_silence_duration_ms}ms")
        print(f"{'='*60}\n")

        try:
            # 오디오 파일 로드
            wav, sr = torchaudio.load(audio_path)

            # 모노 변환
            if wav.shape[0] > 1:
                wav = wav.mean(dim=0, keepdim=True)

            # 샘플레이트 변환 (16kHz)
            if sr != self._sample_rate:
                resampler = torchaudio.transforms.Resample(sr, self._sample_rate)
                wav = resampler(wav)
                sr = self._sample_rate

            original_duration = wav.shape[1] / sr

            # VAD로 음성 구간 감지
            speech_timestamps = get_speech_timestamps(
                wav.squeeze(),
                self._model,
                threshold=threshold,
                sampling_rate=sr,
                min_speech_duration_ms=min_speech_duration_ms,
                min_silence_duration_ms=min_silence_duration_ms,
            )

            # 음성 구간을 VADSegment로 변환
            segments = [
                VADSegment(
                    start=ts["start"] / sr,
                    end=ts["end"] / sr,
                )
                for ts in speech_timestamps
            ]

            # 음성 구간만 추출
            if speech_timestamps:
                processed_wav = collect_chunks(speech_timestamps, wav.squeeze())
                processed_duration = len(processed_wav) / sr
            else:
                # 음성이 없으면 빈 오디오
                processed_wav = torch.zeros(sr)  # 1초 무음
                processed_duration = 1.0

            # 출력 파일 경로 생성
            if output_path is None:
                input_path = Path(audio_path)
                output_path = str(input_path.parent / f"{input_path.stem}_vad{input_path.suffix}")

            # 처리된 오디오 저장
            torchaudio.save(
                output_path,
                processed_wav.unsqueeze(0),
                sr,
            )

            silence_removed = original_duration - processed_duration
            processing_time = time.time() - start_time

            # 상세 로깅
            print(f"\n{'='*60}")
            print(f"✅ VAD Processing Completed")
            print(f"{'='*60}")
            print(f"📊 Audio Statistics:")
            print(f"   Original Duration: {original_duration:.2f}s")
            print(f"   Processed Duration: {processed_duration:.2f}s")
            print(f"   Silence Removed: {silence_removed:.2f}s ({silence_removed/original_duration*100:.1f}%)")
            print(f"   Speech Segments: {len(segments)}")
            print(f"   Processing Time: {processing_time:.2f}s")

            if segments:
                print(f"\n🎤 Speech Segments Preview (first 5):")
                for i, seg in enumerate(segments[:5]):
                    print(f"   [{i+1}] {seg.start:.2f}s - {seg.end:.2f}s (duration: {seg.end - seg.start:.2f}s)")

            print(f"{'='*60}\n")

            return VADResult(
                segments=segments,
                original_duration=original_duration,
                processed_duration=processed_duration,
                silence_removed=silence_removed,
                processing_time=processing_time,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ VAD processing failed: {e}")
            raise

    def get_info(self) -> ModelInfo:
        """모델 정보 반환"""
        return ModelInfo(
            name="silero-vad",
            version="6.2.3",
            loaded=self._loaded,
            device="CPU (PyTorch)" if self._loaded else "not_loaded",
        )

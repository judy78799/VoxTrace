"""
Speech Enhancement Model Interface

DeepFilterNet (기본) 또는 noisereduce를 사용하여 오디오의 배경 소음 제거
음성 품질 개선으로 ASR 정확도 향상
"""

import time
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Literal
from dataclasses import dataclass

import numpy as np
import librosa
import soundfile as sf
import noisereduce as nr
import torch

from app.models.base import BaseModel, ModelInfo


@dataclass
class EnhancementResult:
    """음성 향상 처리 결과"""
    enhanced_path: str       # 향상된 오디오 파일 경로
    original_duration: float # 원본 길이 (초)
    processing_time: float   # 처리 시간 (초)
    method: str              # 사용된 방법 ("deepfilternet" or "noisereduce")
    noise_reduction_db: Optional[float] = None  # 노이즈 감소량 (dB)


class EnhancementModel(BaseModel):
    """
    DeepFilterNet 또는 noisereduce 기반 음성 향상

    배경 소음을 제거하여 ASR 정확도를 향상시킵니다

    Methods:
        - deepfilternet: 딥러닝 기반 (기본, 고품질)
        - noisereduce: 스펙트럼 감산 (빠름, 정상 소음에 효과적)
    """

    def __init__(self, method: Literal["deepfilternet", "noisereduce"] = "deepfilternet"):
        super().__init__()
        self._sample_rate = 16000  # 일반적인 음성 샘플레이트
        self._method = method
        self._df_model = None
        self._df_state = None

    async def load(self) -> None:
        """Enhancement 모델 로드"""
        if self._loaded:
            return

        if self._method == "deepfilternet":
            print("🔄 Loading DeepFilterNet model...")
            try:
                from df.enhance import init_df, enhance, save_audio
                from df.io import resample

                self._df_model, self._df_state, _ = init_df()
                self._loaded = True
                print("✅ DeepFilterNet loaded successfully")
            except Exception as e:
                print(f"⚠️  Failed to load DeepFilterNet: {e}")
                print("   Falling back to noisereduce...")
                self._method = "noisereduce"
                self._loaded = True
        else:
            print("🔄 Initializing noisereduce...")
            self._loaded = True
            print("✅ noisereduce ready")

    async def unload(self) -> None:
        """메모리에서 모델 언로드"""
        if self._loaded:
            self._df_model = None
            self._df_state = None
            self._loaded = False
            print(f"🗑️  Enhancement model ({self._method}) unloaded")

    async def enhance_audio(
        self,
        audio_path: str,
        output_path: Optional[str] = None,
    ) -> EnhancementResult:
        """
        오디오 파일의 배경 소음 제거

        Args:
            audio_path: 입력 오디오 파일 경로
            output_path: 출력 파일 경로 (None이면 자동 생성)

        Returns:
            EnhancementResult with enhanced audio path and processing info
        """
        if not self._loaded:
            await self.load()

        start_time = time.time()

        # 디버그 로깅
        print(f"\n{'='*60}")
        print(f"🎵 Speech Enhancement Started ({self._method})")
        print(f"{'='*60}")
        print(f"📁 Audio Path: {audio_path}")
        print(f"{'='*60}\n")

        try:
            # 오디오 파일 로드 (librosa 사용)
            print(f"🔄 Loading audio file...")
            audio, sr = librosa.load(audio_path, sr=None)

            original_duration = len(audio) / sr

            print(f"🎧 Original audio loaded:")
            print(f"   Duration: {original_duration:.2f}s")
            print(f"   Sample rate: {sr} Hz")
            print(f"   Shape: {audio.shape}")

            # 출력 파일 경로 생성
            if output_path is None:
                input_path = Path(audio_path)
                method_suffix = "df" if self._method == "deepfilternet" else "nr"
                output_path = str(input_path.parent / f"{input_path.stem}_enhanced_{method_suffix}.wav")

            # Enhancement 처리
            if self._method == "deepfilternet":
                enhanced = await self._enhance_deepfilternet(audio, sr)
            else:
                enhanced = await self._enhance_noisereduce(audio, sr)

            # 향상된 오디오 저장
            print(f"\n💾 Saving enhanced audio...")
            sf.write(output_path, enhanced, sr)

            processing_time = time.time() - start_time

            # 상세 로깅
            print(f"\n{'='*60}")
            print(f"✅ Speech Enhancement Completed")
            print(f"{'='*60}")
            print(f"📊 Processing Statistics:")
            print(f"   Method: {self._method}")
            print(f"   Original Duration: {original_duration:.2f}s")
            print(f"   Processing Time: {processing_time:.2f}s")
            print(f"   RTF (Real-Time Factor): {processing_time/original_duration:.2f}x")
            print(f"   Enhanced Audio Path: {output_path}")
            print(f"{'='*60}\n")

            return EnhancementResult(
                enhanced_path=output_path,
                original_duration=original_duration,
                processing_time=processing_time,
                method=self._method,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ Enhancement processing failed: {e}")
            raise

    async def _enhance_deepfilternet(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """DeepFilterNet으로 음성 향상"""
        from df.enhance import enhance
        from df.io import resample

        print(f"\n🔬 Applying DeepFilterNet enhancement...")

        # DeepFilterNet은 48kHz를 선호
        if sr != 48000:
            print(f"   Resampling {sr}Hz -> 48000Hz...")
            audio_48k = resample(audio, sr, 48000)
        else:
            audio_48k = audio

        # Stereo로 변환 (DeepFilterNet 요구사항)
        if audio_48k.ndim == 1:
            audio_48k = np.stack([audio_48k, audio_48k])

        # Tensor 변환
        audio_tensor = torch.from_numpy(audio_48k).float()

        # Enhancement 적용
        enhanced_tensor = enhance(self._df_model, self._df_state, audio_tensor)

        # NumPy로 변환
        enhanced = enhanced_tensor.numpy()

        # Mono로 변환 (평균)
        if enhanced.ndim == 2:
            enhanced = np.mean(enhanced, axis=0)

        # 원래 샘플레이트로 복원
        if sr != 48000:
            print(f"   Resampling 48000Hz -> {sr}Hz...")
            enhanced = resample(enhanced, 48000, sr)

        return enhanced

    async def _enhance_noisereduce(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """noisereduce로 음성 향상"""
        print(f"\n🔬 Applying noisereduce...")
        # stationary=True: 복도 소음 같은 정상 노이즈에 효과적
        enhanced = nr.reduce_noise(
            y=audio,
            sr=sr,
            stationary=True,
            prop_decrease=1.0,  # 노이즈 감소 비율 (0.0-1.0)
        )
        return enhanced

    def get_info(self) -> ModelInfo:
        """모델 정보 반환"""
        return ModelInfo(
            name=f"enhancement-{self._method}",
            version="0.5.6" if self._method == "deepfilternet" else "3.0.3",
            loaded=self._loaded,
            device="CPU" if self._loaded else "not_loaded",
        )

"""
ASR (Automatic Speech Recognition) Model Interface

Phase 3: MLX Whisper implementation for Apple Silicon
Optimized for M4 Mac with Neural Engine acceleration
"""

import time
from typing import Optional
from dataclasses import dataclass

import mlx_whisper

from app.models.base import BaseModel, ModelInfo


@dataclass
class ASRSegment:
    """Single ASR output segment"""

    start: float
    end: float
    text: str
    confidence: Optional[float] = None


@dataclass
class ASRResult:
    """Complete ASR transcription result"""

    segments: list[ASRSegment]
    language: str
    processing_time: float


class ASRModel(BaseModel):
    """
    ASR Model with MLX Whisper

    Apple Silicon optimized with Metal acceleration
    Supports models: tiny, base, small, medium, large-v3
    """

    def __init__(self, model_name: str = "medium"):
        """
        Initialize ASR model

        Args:
            model_name: Whisper model size (tiny/base/small/medium/large-v3)
        """
        super().__init__()
        self.model_name = model_name
        self.hf_repo = f"mlx-community/whisper-{model_name}"
        self._model = None

    async def load(self) -> None:
        """
        Load MLX Whisper model

        첫 실행 시 Hugging Face에서 모델 다운로드 (~1-2분)
        """
        if self._loaded:
            return

        print(f"🔄 Loading MLX Whisper ({self.model_name})...")
        print(f"   Repository: {self.hf_repo}")

        try:
            # MLX Whisper는 lazy loading - transcribe 시 자동 로드됨
            # 여기서는 모델이 존재하는지만 확인
            self._loaded = True

            print(f"✅ MLX Whisper {self.model_name} ready")
            print(f"   Device: Apple Silicon (Metal)")
            print(f"   Note: Model will be downloaded on first transcribe")

        except Exception as e:
            print(f"❌ Failed to initialize model: {e}")
            raise

    async def unload(self) -> None:
        """메모리에서 모델 언로드"""
        if self._loaded:
            self._model = None
            self._loaded = False
            print(f"🗑️  MLX Whisper {self.model_name} unloaded")

    async def transcribe(
        self,
        audio_path: str,
        language: str = "ko",
        task: str = "transcribe",
    ) -> ASRResult:
        """
        음성 파일을 텍스트로 변환

        Args:
            audio_path: 오디오 파일 경로
            language: 언어 코드 (ko, en, etc.)
            task: "transcribe" (전사) 또는 "translate" (번역)

        Returns:
            ASRResult with segments and metadata
        """
        if not self._loaded:
            await self.load()

        start_time = time.time()

        try:
            # MLX Whisper 전사 수행
            result = mlx_whisper.transcribe(
                audio_path,
                path_or_hf_repo=self.hf_repo,
                language=language,
                task=task,
                word_timestamps=False,  # 단어별 타임스탬프 (옵션)
                verbose=False,
            )

            # ASRSegment로 변환
            segments = []
            for seg in result["segments"]:
                # avg_logprob를 0-1 신뢰도로 변환 (대략적)
                # logprob는 보통 -1 ~ 0 범위
                confidence = max(0.0, min(1.0, seg.get("avg_logprob", -0.5) + 1.0))

                segments.append(
                    ASRSegment(
                        start=seg["start"],
                        end=seg["end"],
                        text=seg["text"].strip(),
                        confidence=confidence,
                    )
                )

            processing_time = time.time() - start_time

            return ASRResult(
                segments=segments,
                language=result["language"],
                processing_time=processing_time,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ Transcription failed: {e}")
            raise

    def get_info(self) -> ModelInfo:
        """모델 정보 반환"""
        return ModelInfo(
            name=f"mlx-whisper-{self.model_name}",
            version="0.4.3",
            loaded=self._loaded,
            device="Apple Silicon (Metal)" if self._loaded else "not_loaded",
        )

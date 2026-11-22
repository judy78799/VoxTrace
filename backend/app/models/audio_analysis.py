"""
Audio Signal Analysis Module

오디오 신호 품질 분석:
- SNR (Signal-to-Noise Ratio) 계산
- 스펙트로그램 생성
- 주파수 분석
- 음성 에너지 분포
- 클리핑/왜곡 감지
"""

import io
import base64
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

import numpy as np
import librosa
import librosa.display
import matplotlib
matplotlib.use('Agg')  # 백엔드 설정 (GUI 없이 사용)
import matplotlib.pyplot as plt

from app.models.base import BaseModel, ModelInfo


@dataclass
class FrequencyAnalysis:
    """주파수 분석 결과"""
    low_freq_energy: float      # 저주파 에너지 (0-300Hz)
    mid_freq_energy: float       # 중간 주파수 에너지 (300-3000Hz)
    high_freq_energy: float      # 고주파 에너지 (3000Hz+)
    spectral_centroid: float     # 스펙트럼 중심 (Hz)
    spectral_rolloff: float      # 스펙트럼 롤오프 (Hz)
    spectral_bandwidth: float    # 스펙트럼 대역폭 (Hz)


@dataclass
class AudioAnalysisResult:
    """오디오 분석 결과"""
    # SNR 관련
    snr_db: Optional[float] = None           # Signal-to-Noise Ratio (dB)

    # 주파수 분석
    frequency_analysis: Optional[FrequencyAnalysis] = None

    # 클리핑/왜곡 감지
    clipping_detected: bool = False
    clipping_percentage: float = 0.0

    # 음성 에너지
    rms_energy: float = 0.0                  # RMS (Root Mean Square) 에너지
    zero_crossing_rate: float = 0.0          # 영교차율

    # 스펙트로그램 (Base64 인코딩된 PNG)
    spectrogram_base64: Optional[str] = None

    # 추가 메타데이터
    duration: float = 0.0
    sample_rate: int = 0

    # VAD 기반 음성 분석
    speech_ratio: Optional[float] = None     # 전체 중 음성 비율 (0.0-1.0)
    speech_segments_count: Optional[int] = None  # 음성 구간 개수

    # 잔향 분석
    reverberation_level: Optional[str] = None  # 'none', 'low', 'medium', 'high'
    reverberation_time_ms: Optional[float] = None  # RT60 (밀리초)

    # 다중 화자 중첩
    overlapping_speech_detected: bool = False
    overlapping_speech_ratio: Optional[float] = None  # 중첩 구간 비율

    # 품질 평가
    quality_score: float = 0.0               # 0-100 점수
    quality_issues: list[str] = None         # 감지된 문제들
    noise_level: Optional[str] = None        # 'low', 'medium', 'high', 'very_high'
    speech_quality: Optional[str] = None     # 'excellent', 'good', 'fair', 'poor'


class AudioAnalysisModel(BaseModel):
    """
    오디오 신호 분석 모델

    음성 품질을 정량적으로 평가하여 ASR 성능 예측 및 개선 방향 제시
    """

    def __init__(self, vad_model=None):
        super().__init__()
        self._loaded = True  # 별도 모델 로딩 불필요
        self._vad_model = vad_model  # VAD 모델 (옵션)

    async def load(self) -> None:
        """모델 로딩 (불필요)"""
        self._loaded = True

    async def unload(self) -> None:
        """모델 언로드"""
        self._loaded = False

    async def analyze(
        self,
        audio_path: str,
        generate_spectrogram: bool = True,
        enable_vad_analysis: bool = True,
        enable_reverberation: bool = True,
        enable_overlap_detection: bool = False,  # 더 느림
    ) -> AudioAnalysisResult:
        """
        오디오 신호 분석

        Args:
            audio_path: 오디오 파일 경로
            generate_spectrogram: 스펙트로그램 생성 여부
            enable_vad_analysis: VAD 기반 음성 비율 분석
            enable_reverberation: 잔향 분석
            enable_overlap_detection: 다중 화자 중첩 감지

        Returns:
            AudioAnalysisResult with analysis metrics
        """
        print(f"\n{'='*60}")
        print(f"🔬 Audio Signal Analysis Started")
        print(f"{'='*60}")
        print(f"📁 Audio Path: {audio_path}")
        print(f"{'='*60}\n")

        try:
            # 오디오 로드 (원본 샘플레이트 유지)
            y, sr = librosa.load(audio_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)

            print(f"✅ Audio loaded: {duration:.2f}s @ {sr}Hz")

            # 1. SNR 계산
            snr_db = self._calculate_snr(y)

            # 2. 주파수 분석
            freq_analysis = self._analyze_frequency(y, sr)

            # 3. 클리핑 감지
            clipping_detected, clipping_pct = self._detect_clipping(y)

            # 4. 음성 에너지
            rms_energy = float(np.mean(librosa.feature.rms(y=y)))
            zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))

            # 5. VAD 기반 음성 분석
            speech_ratio = None
            speech_segments_count = None
            if enable_vad_analysis and self._vad_model:
                speech_ratio, speech_segments_count = await self._analyze_speech_ratio(audio_path)

            # 6. 잔향 분석
            reverb_level = None
            reverb_time_ms = None
            if enable_reverberation:
                reverb_level, reverb_time_ms = self._analyze_reverberation(y, sr)

            # 7. 다중 화자 중첩 감지 (옵션)
            overlap_detected = False
            overlap_ratio = None
            if enable_overlap_detection:
                overlap_detected, overlap_ratio = self._detect_overlapping_speech(y, sr)

            # 8. 스펙트로그램 생성 (옵션)
            spectrogram_base64 = None
            if generate_spectrogram:
                spectrogram_base64 = self._generate_spectrogram(y, sr)

            # 9. 종합 품질 평가
            quality_score, quality_issues, noise_level, speech_quality = self._evaluate_quality_comprehensive(
                snr_db=snr_db,
                clipping_detected=clipping_detected,
                clipping_pct=clipping_pct,
                freq_analysis=freq_analysis,
                speech_ratio=speech_ratio,
                reverb_level=reverb_level,
                overlap_detected=overlap_detected,
            )

            # 결과 출력
            print(f"\n{'='*60}")
            print(f"📊 Analysis Results")
            print(f"{'='*60}")
            print(f"🔊 SNR: {snr_db:.2f} dB" if snr_db else "🔊 SNR: N/A")
            print(f"⚡ RMS Energy: {rms_energy:.4f}")
            print(f"🌊 Zero Crossing Rate: {zcr:.4f}")
            if speech_ratio is not None:
                print(f"🎤 Speech Ratio: {speech_ratio*100:.1f}% ({speech_segments_count} segments)")
            if reverb_level:
                print(f"🏢 Reverberation: {reverb_level} ({reverb_time_ms:.0f}ms)")
            if overlap_detected:
                print(f"👥 Overlapping Speech: {overlap_ratio*100:.1f}%")
            print(f"📈 Quality Score: {quality_score:.1f}/100")
            print(f"🔇 Noise Level: {noise_level}")
            print(f"🎯 Speech Quality: {speech_quality}")

            if clipping_detected:
                print(f"⚠️  Clipping Detected: {clipping_pct:.2f}%")

            if quality_issues:
                print(f"\n❌ Quality Issues:")
                for issue in quality_issues:
                    print(f"   - {issue}")

            print(f"{'='*60}\n")

            return AudioAnalysisResult(
                snr_db=snr_db,
                frequency_analysis=freq_analysis,
                clipping_detected=clipping_detected,
                clipping_percentage=clipping_pct,
                rms_energy=rms_energy,
                zero_crossing_rate=zcr,
                speech_ratio=speech_ratio,
                speech_segments_count=speech_segments_count,
                reverberation_level=reverb_level,
                reverberation_time_ms=reverb_time_ms,
                overlapping_speech_detected=overlap_detected,
                overlapping_speech_ratio=overlap_ratio,
                spectrogram_base64=spectrogram_base64,
                duration=duration,
                sample_rate=sr,
                quality_score=quality_score,
                quality_issues=quality_issues or [],
                noise_level=noise_level,
                speech_quality=speech_quality,
            )

        except Exception as e:
            print(f"❌ Audio analysis failed: {e}")
            raise

    def _calculate_snr(self, y: np.ndarray) -> Optional[float]:
        """
        SNR 계산

        음성 구간의 에너지와 무음 구간의 노이즈 에너지 비율
        """
        try:
            # RMS 에너지 계산
            rms = librosa.feature.rms(y=y)[0]

            # 상위 50%를 신호, 하위 20%를 노이즈로 가정
            signal_power = np.mean(np.sort(rms)[-len(rms)//2:] ** 2)
            noise_power = np.mean(np.sort(rms)[:len(rms)//5] ** 2)

            if noise_power > 0:
                snr = 10 * np.log10(signal_power / noise_power)
                return float(snr)
            else:
                return None

        except Exception as e:
            print(f"⚠️  SNR calculation failed: {e}")
            return None

    def _analyze_frequency(self, y: np.ndarray, sr: int) -> FrequencyAnalysis:
        """주파수 영역 분석"""
        # FFT로 주파수 스펙트럼 계산
        S = np.abs(librosa.stft(y))
        freqs = librosa.fft_frequencies(sr=sr)

        # 주파수 대역별 에너지
        low_mask = freqs < 300
        mid_mask = (freqs >= 300) & (freqs < 3000)
        high_mask = freqs >= 3000

        low_energy = float(np.mean(S[low_mask]))
        mid_energy = float(np.mean(S[mid_mask]))
        high_energy = float(np.mean(S[high_mask]))

        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]

        return FrequencyAnalysis(
            low_freq_energy=low_energy,
            mid_freq_energy=mid_energy,
            high_freq_energy=high_energy,
            spectral_centroid=float(np.mean(spectral_centroids)),
            spectral_rolloff=float(np.mean(spectral_rolloff)),
            spectral_bandwidth=float(np.mean(spectral_bandwidth)),
        )

    def _detect_clipping(self, y: np.ndarray) -> tuple[bool, float]:
        """
        클리핑 감지

        신호가 최대값에 근접하면 클리핑으로 판단
        """
        threshold = 0.99
        clipped_samples = np.sum(np.abs(y) > threshold)
        clipping_pct = (clipped_samples / len(y)) * 100

        clipping_detected = clipping_pct > 0.1  # 0.1% 이상이면 문제

        return clipping_detected, float(clipping_pct)

    def _generate_spectrogram(self, y: np.ndarray, sr: int) -> str:
        """
        스펙트로그램 생성 (Base64 인코딩된 PNG)
        """
        try:
            # 멜 스펙트로그램 생성
            S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
            S_dB = librosa.power_to_db(S, ref=np.max)

            # 플롯 생성
            plt.figure(figsize=(12, 6))
            librosa.display.specshow(
                S_dB,
                sr=sr,
                x_axis='time',
                y_axis='mel',
                cmap='viridis'
            )
            plt.colorbar(format='%+2.0f dB')
            plt.title('Mel Spectrogram')
            plt.tight_layout()

            # PNG로 변환 후 Base64 인코딩
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()

            return img_base64

        except Exception as e:
            print(f"⚠️  Spectrogram generation failed: {e}")
            return None

    async def _analyze_speech_ratio(self, audio_path: str) -> tuple[Optional[float], Optional[int]]:
        """
        VAD를 사용한 음성 비율 분석

        Returns:
            (speech_ratio, segments_count)
        """
        try:
            if not self._vad_model:
                return None, None

            # VAD로 음성 구간 감지 (파일은 생성하지 않음)
            from silero_vad import get_speech_timestamps
            import torch
            import torchaudio

            # 오디오 로드
            wav, sr = torchaudio.load(audio_path)
            if wav.shape[0] > 1:
                wav = wav.mean(dim=0, keepdim=True)

            # 16kHz로 리샘플링
            if sr != 16000:
                resampler = torchaudio.transforms.Resample(sr, 16000)
                wav = resampler(wav)
                sr = 16000

            # VAD 모델 로드 (lazy)
            if not self._vad_model._loaded:
                await self._vad_model.load()

            # 음성 구간 감지
            speech_timestamps = get_speech_timestamps(
                wav.squeeze(),
                self._vad_model._model,
                threshold=0.5,
                sampling_rate=sr,
            )

            # 음성 비율 계산
            if speech_timestamps:
                total_speech_samples = sum(ts["end"] - ts["start"] for ts in speech_timestamps)
                total_samples = wav.shape[1]
                speech_ratio = total_speech_samples / total_samples if total_samples > 0 else 0
                return float(speech_ratio), len(speech_timestamps)
            else:
                return 0.0, 0

        except Exception as e:
            print(f"⚠️  Speech ratio analysis failed: {e}")
            return None, None

    def _analyze_reverberation(self, y: np.ndarray, sr: int) -> tuple[Optional[str], Optional[float]]:
        """
        잔향 분석

        간단한 방법: 에너지 감쇄율을 기반으로 잔향 추정

        Returns:
            (reverberation_level, rt60_ms)
        """
        try:
            # RMS 에너지 계산
            rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]

            # 에너지 감쇄 분석
            # 피크 이후의 감쇄 시간 계산
            if len(rms) < 10:
                return "none", 0.0

            # 평균 감쇄율 계산
            decay_rates = []
            for i in range(len(rms) - 1):
                if rms[i] > 0:
                    decay_rate = abs(rms[i+1] - rms[i]) / rms[i]
                    decay_rates.append(decay_rate)

            avg_decay_rate = np.mean(decay_rates) if decay_rates else 0

            # 감쇄율 기반 잔향 추정
            # 느린 감쇄 = 높은 잔향
            if avg_decay_rate < 0.05:
                reverb_level = "high"
                rt60_ms = 500  # 추정값
            elif avg_decay_rate < 0.1:
                reverb_level = "medium"
                rt60_ms = 300
            elif avg_decay_rate < 0.2:
                reverb_level = "low"
                rt60_ms = 150
            else:
                reverb_level = "none"
                rt60_ms = 50

            return reverb_level, rt60_ms

        except Exception as e:
            print(f"⚠️  Reverberation analysis failed: {e}")
            return None, None

    def _detect_overlapping_speech(self, y: np.ndarray, sr: int) -> tuple[bool, Optional[float]]:
        """
        다중 화자 중첩 감지

        간단한 방법: 고주파 에너지 변동 패턴 분석
        (실제로는 pyannote 등이 필요하지만, 여기서는 근사값)

        Returns:
            (overlap_detected, overlap_ratio)
        """
        try:
            # 스펙트럼 플럭스 계산
            S = np.abs(librosa.stft(y))
            spectral_flux = np.sqrt(np.sum(np.diff(S, axis=1)**2, axis=0))

            # 높은 변동성 구간 = 중첩 가능성
            flux_threshold = np.percentile(spectral_flux, 80)
            high_flux_frames = spectral_flux > flux_threshold

            overlap_ratio = np.sum(high_flux_frames) / len(high_flux_frames) if len(high_flux_frames) > 0 else 0

            # 20% 이상 높은 변동성 = 중첩 가능성
            overlap_detected = overlap_ratio > 0.2

            return overlap_detected, float(overlap_ratio)

        except Exception as e:
            print(f"⚠️  Overlap detection failed: {e}")
            return False, None

    def _evaluate_quality_comprehensive(
        self,
        snr_db: Optional[float],
        clipping_detected: bool,
        clipping_pct: float,
        freq_analysis: FrequencyAnalysis,
        speech_ratio: Optional[float],
        reverb_level: Optional[str],
        overlap_detected: bool,
    ) -> tuple[float, list[str], str, str]:
        """
        종합 품질 평가 (확장 버전)

        Returns:
            (quality_score, quality_issues, noise_level, speech_quality)
        """
        score = 100.0
        issues = []

        # 1. SNR 평가 및 노이즈 레벨 분류
        noise_level = "low"
        if snr_db is not None:
            if snr_db < 5:
                score -= 40
                issues.append(f"매우 낮은 SNR ({snr_db:.1f} dB) - 배경 소음이 매우 큽니다")
                noise_level = "very_high"
            elif snr_db < 10:
                score -= 30
                issues.append(f"낮은 SNR ({snr_db:.1f} dB) - 배경 소음이 큽니다")
                noise_level = "high"
            elif snr_db < 15:
                score -= 15
                issues.append(f"보통 SNR ({snr_db:.1f} dB) - 배경 소음이 있습니다")
                noise_level = "medium"
            elif snr_db < 20:
                score -= 5
                noise_level = "low"

        # 2. 클리핑 평가
        if clipping_detected:
            if clipping_pct > 1.0:
                score -= 25
                issues.append(f"심각한 클리핑 ({clipping_pct:.2f}%) - 음성 왜곡")
            else:
                score -= 10
                issues.append(f"클리핑 감지 ({clipping_pct:.2f}%)")

        # 3. 주파수 분포 평가
        total_energy = (
            freq_analysis.low_freq_energy +
            freq_analysis.mid_freq_energy +
            freq_analysis.high_freq_energy
        )

        if total_energy > 0:
            mid_ratio = freq_analysis.mid_freq_energy / total_energy
            if mid_ratio < 0.4:
                score -= 15
                issues.append("음성 주파수 대역 에너지 부족 - 녹음 품질 저하")

            low_ratio = freq_analysis.low_freq_energy / total_energy
            if low_ratio > 0.4:
                score -= 10
                issues.append("저주파 노이즈 감지 - 에어컨, 차량 소음 등")

        # 4. 음성 비율 평가
        if speech_ratio is not None:
            if speech_ratio < 0.3:
                score -= 15
                issues.append(f"음성 비율 낮음 ({speech_ratio*100:.1f}%) - 긴 무음 구간")
            elif speech_ratio < 0.5:
                score -= 5
                issues.append(f"음성 비율 보통 ({speech_ratio*100:.1f}%)")

        # 5. 잔향 평가
        if reverb_level == "high":
            score -= 20
            issues.append("높은 잔향 - 넓은 공간 또는 울림")
        elif reverb_level == "medium":
            score -= 10
            issues.append("중간 잔향 - 약간의 울림")

        # 6. 화자 중첩 평가
        if overlap_detected:
            score -= 15
            issues.append("다중 화자 중첩 가능성 감지")

        score = max(0, min(100, score))

        # 종합 품질 판정
        if score >= 80:
            speech_quality = "excellent"
        elif score >= 65:
            speech_quality = "good"
        elif score >= 45:
            speech_quality = "fair"
        else:
            speech_quality = "poor"

        return score, issues, noise_level, speech_quality

    def _evaluate_quality(
        self,
        snr_db: Optional[float],
        clipping_detected: bool,
        clipping_pct: float,
        freq_analysis: FrequencyAnalysis,
    ) -> tuple[float, list[str]]:
        """
        전체 품질 평가 (기존 호환성 유지)

        Returns:
            (quality_score, quality_issues)
        """
        score, issues, _, _ = self._evaluate_quality_comprehensive(
            snr_db=snr_db,
            clipping_detected=clipping_detected,
            clipping_pct=clipping_pct,
            freq_analysis=freq_analysis,
            speech_ratio=None,
            reverb_level=None,
            overlap_detected=False,
        )
        return score, issues

    def get_info(self) -> ModelInfo:
        """모델 정보 반환"""
        return ModelInfo(
            name="audio-analysis",
            version="1.0.0",
            loaded=self._loaded,
            device="CPU (NumPy/Librosa)",
        )

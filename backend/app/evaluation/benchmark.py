"""
Benchmarking System

모델 성능 벤치마크 실행 및 리소스 모니터링
"""

import time
import psutil
import platform
from typing import Dict, Optional, Any
from contextlib import contextmanager
from dataclasses import dataclass, asdict


@dataclass
class ResourceUsage:
    """시스템 리소스 사용량"""

    peak_memory_mb: float
    avg_memory_mb: float
    cpu_percent: float
    platform_info: str


class ResourceMonitor:
    """
    시스템 리소스 모니터링

    메모리, CPU 사용량 추적
    """

    def __init__(self):
        self.process = psutil.Process()
        self.start_memory = 0.0
        self.peak_memory = 0.0
        self.memory_samples = []
        self.cpu_samples = []

    def start(self):
        """모니터링 시작"""
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.start_memory
        self.memory_samples = [self.start_memory]
        self.cpu_samples = []

    def sample(self):
        """현재 리소스 사용량 샘플링"""
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        current_cpu = self.process.cpu_percent(interval=0.1)

        self.memory_samples.append(current_memory)
        self.cpu_samples.append(current_cpu)

        if current_memory > self.peak_memory:
            self.peak_memory = current_memory

    def get_usage(self) -> ResourceUsage:
        """누적된 리소스 사용량 반환"""
        avg_memory = (
            sum(self.memory_samples) / len(self.memory_samples)
            if self.memory_samples
            else 0.0
        )
        avg_cpu = (
            sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0.0
        )

        return ResourceUsage(
            peak_memory_mb=self.peak_memory,
            avg_memory_mb=avg_memory,
            cpu_percent=avg_cpu,
            platform_info=self._get_platform_info(),
        )

    def _get_platform_info(self) -> str:
        """플랫폼 정보 수집"""
        system = platform.system()
        machine = platform.machine()
        processor = platform.processor()

        # M4 Mac 감지
        if system == "Darwin" and "arm" in machine.lower():
            return f"Apple Silicon {machine} ({processor})"
        return f"{system} {machine}"


@contextmanager
def monitor_resources():
    """
    리소스 모니터링 컨텍스트 매니저

    Usage:
        with monitor_resources() as monitor:
            # 모델 실행
            result = model.transcribe(audio)
            monitor.sample()

        usage = monitor.get_usage()
    """
    monitor = ResourceMonitor()
    monitor.start()
    try:
        yield monitor
    finally:
        monitor.sample()


class BenchmarkRunner:
    """
    모델 벤치마크 실행기

    통일된 방식으로 모델 성능 측정
    """

    def __init__(self, warmup_runs: int = 1):
        """
        Args:
            warmup_runs: 워밍업 실행 횟수 (첫 실행은 모델 로딩 시간 포함)
        """
        self.warmup_runs = warmup_runs

    async def run_asr_benchmark(
        self,
        model: Any,
        audio_path: str,
        ground_truth: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        ASR 모델 벤치마크

        Args:
            model: ASR 모델 인스턴스
            audio_path: 테스트 음성 파일 경로
            ground_truth: 정답 텍스트 (CER/WER 계산용)

        Returns:
            {
                "transcription": "전사 결과",
                "processing_time": 2.35,
                "rtf": 0.25,
                "cer": 12.5,
                "wer": 18.3,
                "resource_usage": {...}
            }
        """
        from app.evaluation.metrics import calculate_cer, calculate_wer, calculate_rtf

        # Warmup
        if self.warmup_runs > 0:
            for _ in range(self.warmup_runs):
                await model.transcribe(audio_path)

        # Actual benchmark
        with monitor_resources() as monitor:
            start_time = time.time()

            result = await model.transcribe(audio_path)

            processing_time = time.time() - start_time
            monitor.sample()

        resource_usage = monitor.get_usage()

        # RTF 계산 (audio duration은 모델 결과에서 가져옴)
        audio_duration = sum(
            seg.end - seg.start for seg in result.segments
        )  # 대략적 계산
        rtf = calculate_rtf(processing_time, audio_duration)

        benchmark_result = {
            "transcription": " ".join(seg.text for seg in result.segments),
            "processing_time": processing_time,
            "rtf": rtf,
            "audio_duration": audio_duration,
            "resource_usage": asdict(resource_usage),
        }

        # Ground truth가 있으면 CER/WER 계산
        if ground_truth:
            transcription = benchmark_result["transcription"]
            cer_result = calculate_cer(ground_truth, transcription)
            wer_result = calculate_wer(ground_truth, transcription)

            benchmark_result.update(
                {
                    "cer": cer_result["cer"],
                    "wer": wer_result["wer"],
                    "substitutions": cer_result["substitutions"],
                    "deletions": cer_result["deletions"],
                    "insertions": cer_result["insertions"],
                }
            )

        return benchmark_result

    def compare_models(
        self,
        results: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        여러 모델 결과 비교

        Args:
            results: {"model_A": {...}, "model_B": {...}}

        Returns:
            비교 테이블 및 최고 성능 모델
        """
        comparison = []

        for model_name, result in results.items():
            comparison.append(
                {
                    "model": model_name,
                    "cer": result.get("cer", None),
                    "wer": result.get("wer", None),
                    "rtf": result.get("rtf", None),
                    "peak_memory_mb": result.get("resource_usage", {}).get(
                        "peak_memory_mb", None
                    ),
                }
            )

        # CER 기준 최고 성능 모델
        best_cer = min(
            (r for r in comparison if r["cer"] is not None),
            key=lambda x: x["cer"],
            default=None,
        )

        # RTF 기준 최고 속도 모델
        best_rtf = min(
            (r for r in comparison if r["rtf"] is not None),
            key=lambda x: x["rtf"],
            default=None,
        )

        return {
            "comparison_table": comparison,
            "best_accuracy": best_cer,
            "best_speed": best_rtf,
        }


# Example usage in Phase 3+
"""
from app.models.asr import ASRModel
from app.evaluation.benchmark import BenchmarkRunner

# 모델 준비
model_mlx = ASRModel(model_name="mlx-whisper-small")
model_faster = ASRModel(model_name="faster-whisper-small")

await model_mlx.load()
await model_faster.load()

# 벤치마크 실행
benchmark = BenchmarkRunner(warmup_runs=1)

result_mlx = await benchmark.run_asr_benchmark(
    model=model_mlx,
    audio_path="test_audio.wav",
    ground_truth="오늘 회의는 오후 3시에 시작합니다"
)

result_faster = await benchmark.run_asr_benchmark(
    model=model_faster,
    audio_path="test_audio.wav",
    ground_truth="오늘 회의는 오후 3시에 시작합니다"
)

# 비교
comparison = benchmark.compare_models({
    "MLX Whisper": result_mlx,
    "Faster Whisper": result_faster
})

print(f"Best accuracy: {comparison['best_accuracy']['model']} (CER: {comparison['best_accuracy']['cer']:.1%})")
print(f"Best speed: {comparison['best_speed']['model']} (RTF: {comparison['best_speed']['rtf']:.2f})")
"""

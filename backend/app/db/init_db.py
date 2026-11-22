"""
Database Initialization

첫 실행 시 데이터베이스 테이블 자동 생성
"""

import asyncio
from pathlib import Path

from app.db.base import engine, Base
from app.db.models import (
    Project,
    AudioFile,
    ProcessedAudio,
    Transcript,
    TranscriptSegment,
    TranscriptEdit,
    AudioQualityAnalysis,
    EvaluationDataset,
    ExperimentConfig,
    Evaluation,
    ModelBenchmark,
)


async def init_db():
    """
    데이터베이스 준비 (기존 데이터 보존)

    Phase 1에서 정의한 모든 테이블 생성:
    - 기본 테이블: 7개
    - 평가 시스템: 4개
    총 11개 테이블

    주의: create_all()은 존재하지 않는 테이블만 생성하며,
         기존 테이블과 데이터는 절대 삭제하지 않습니다.
    """
    # 데이터 디렉토리 생성
    data_dir = Path("./data")
    db_dir = data_dir / "db"
    uploads_dir = data_dir / "uploads"
    processed_dir = data_dir / "processed"

    db_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    print("📁 데이터 디렉토리 생성 완료")
    print(f"   - Database: {db_dir}")
    print(f"   - Uploads: {uploads_dir}")
    print(f"   - Processed: {processed_dir}")

    # 테이블 생성 (IF NOT EXISTS)
    async with engine.begin() as conn:
        # 존재하지 않는 테이블만 생성 (기존 데이터 보존)
        await conn.run_sync(Base.metadata.create_all)

    print("\n✅ 데이터베이스 준비 완료! (기존 데이터 보존됨)")
    print(f"   SQLite DB: {db_dir / 'voxtrace.db'}")
    print("\n확인된 테이블:")
    print("   기본 테이블:")
    print("   - projects")
    print("   - audio_files")
    print("   - processed_audio")
    print("   - transcripts")
    print("   - transcript_segments")
    print("   - transcript_edits")
    print("   - audio_quality_analysis (NEW)")
    print("\n   평가 시스템:")
    print("   - evaluation_datasets")
    print("   - experiment_configs")
    print("   - evaluations")
    print("   - model_benchmarks")


async def reset_db():
    """
    데이터베이스 초기화 (모든 테이블 삭제 후 재생성)

    ⚠️ 주의: 모든 데이터가 삭제됩니다!
    """
    print("⚠️  데이터베이스 리셋 중...")

    async with engine.begin() as conn:
        # 모든 테이블 삭제
        await conn.run_sync(Base.metadata.drop_all)
        print("   - 기존 테이블 삭제 완료")

        # 테이블 재생성
        await conn.run_sync(Base.metadata.create_all)
        print("   - 테이블 재생성 완료")

    print("✅ 데이터베이스 리셋 완료!")


if __name__ == "__main__":
    # 직접 실행 시 초기화
    print("VoxTrace Database Initialization")
    print("=" * 50)

    asyncio.run(init_db())

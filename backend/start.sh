#!/bin/bash

# VoxTrace Backend Startup Script
# 기존 프로세스 자동 정리 후 백엔드 시작

set -e

PORT=8003

echo "🧹 Cleaning up existing processes..."

# uvicorn 프로세스 정리
pkill -f "uvicorn app.main:app" 2>/dev/null && echo "   ✓ Killed existing uvicorn processes" || echo "   - No existing processes found"

# 1초 대기 (프로세스 종료 시간)
sleep 1

# 포트가 아직 사용 중이면 강제 종료
if lsof -i :$PORT >/dev/null 2>&1; then
    echo "⚠️  Port $PORT still in use, force killing..."
    kill -9 $(lsof -t -i :$PORT) 2>/dev/null || true
    sleep 1
fi

# DB 초기화 확인
if [ ! -f "./data/db/voxtrace.db" ]; then
    echo "📦 Database not found. Initializing..."
    poetry run python -m app.db.init_db
fi

# 백엔드 시작
echo ""
echo "🚀 Starting VoxTrace Backend on port $PORT..."
echo "   Press Ctrl+C to stop"
echo ""

poetry run uvicorn app.main:app --port $PORT --host 127.0.0.1 --reload

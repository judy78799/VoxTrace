#!/bin/bash

# VoxTrace Backend Stop Script

echo "🛑 Stopping VoxTrace Backend..."

# uvicorn 프로세스 종료
if pkill -f "uvicorn app.main:app" 2>/dev/null; then
    echo "   ✓ Backend processes stopped"
else
    echo "   - No running processes found"
fi

# 포트 확인
sleep 1
if lsof -i :8003 >/dev/null 2>&1; then
    echo "⚠️  Port 8003 still in use, force killing..."
    kill -9 $(lsof -t -i :8003) 2>/dev/null || true
    echo "   ✓ Port 8003 cleared"
else
    echo "   ✓ Port 8003 is free"
fi

echo ""
echo "✅ Backend stopped successfully"

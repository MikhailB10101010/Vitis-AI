#!/bin/bash

# ============================================
# Vitis-AI Startup Script
# Скрипт для запуска Backend и Frontend
# ============================================

set -e

echo "🍇 Vitis-AI — Система оценки пригодности земель для виноделия"
echo "=============================================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Файл .env не найден. Копируем из .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Отредактируйте .env и установите необходимые переменные окружения${NC}"
    echo ""
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}📋 Проверка зависимостей...${NC}"

if ! command_exists node; then
    echo -e "${RED}❌ Node.js не установлен. Требуется Node.js >= 18.x${NC}"
    exit 1
fi

if ! command_exists python3; then
    echo -e "${RED}❌ Python не установлен. Требуется Python >= 3.9${NC}"
    exit 1
fi

if ! command_exists mongod && ! command_exists docker; then
    echo -e "${YELLOW}⚠️  MongoDB не найдена. Убедитесь, что MongoDB запущен.${NC}"
fi

echo -e "${GREEN}✅ Зависимости установлены${NC}"
echo ""

# Install Node.js dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}📦 Установка Node.js зависимостей...${NC}"
    npm install
    echo -e "${GREEN}✅ Node.js зависимости установлены${NC}"
    echo ""
fi

# Install Python dependencies if needed
echo -e "${BLUE}🐍 Проверка Python зависимостей...${NC}"
pip3 install -q -r requirements.txt
echo -e "${GREEN}✅ Python зависимости установлены${NC}"
echo ""

# Start MongoDB if using Docker
if command_exists docker && ! pgrep -x "mongod" > /dev/null; then
    echo -e "${BLUE}🐳 Запуск MongoDB через Docker...${NC}"
    docker run -d -p 27017:27017 --name vitis-mongo mongo:latest 2>/dev/null || true
    sleep 3
    echo -e "${GREEN}✅ MongoDB запущен${NC}"
    echo ""
fi

# Start Backend
echo -e "${BLUE}🚀 Запуск Backend сервера...${NC}"
echo -e "${YELLOW}ℹ️  Backend будет доступен на http://localhost:3000${NC}"
node server.js &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Не удалось запустить Backend сервер${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend запущен (PID: $BACKEND_PID)${NC}"
echo ""

# Start Frontend (Streamlit)
echo -e "${BLUE}🎨 Запуск Streamlit интерфейса...${NC}"
echo -e "${YELLOW}ℹ️  Frontend будет доступен на http://localhost:8501${NC}"

cd streamlit_app
streamlit run app.py --server.address localhost --server.port 8501 &
FRONTEND_PID=$!

cd ..

# Wait for frontend to start
sleep 3

# Check if frontend is running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Не удалось запустить Streamlit интерфейс${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo -e "${GREEN}✅ Streamlit запущен (PID: $FRONTEND_PID)${NC}"
echo ""

# Summary
echo "=============================================================="
echo -e "${GREEN}✅ Vitis-AI успешно запущен!${NC}"
echo ""
echo -e "${BLUE}📍 Backend API:${NC} http://localhost:3000"
echo -e "${BLUE}📍 Frontend UI:${NC} http://localhost:8501"
echo -e "${BLUE}📍 Health Check:${NC} http://localhost:3000/health"
echo ""
echo -e "${YELLOW}ℹ️  Для остановки нажмите Ctrl+C${NC}"
echo "=============================================================="
echo ""

# Trap to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Остановка сервисов...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    
    # Stop MongoDB if started via Docker
    if command_exists docker && docker ps -q -f name=vitis-mongo | grep -q .; then
        docker stop vitis-mongo 2>/dev/null
    fi
    
    echo -e "${GREEN}✅ Все сервисы остановлены${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for processes
wait

#!/usr/bin/env bash
# ==============================================================================
# CodeBridge V1 — All-in-One Check & Startup Launcher
# Local Codebase Analyzer by Vanaila
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p "$SCRIPT_DIR/.logs"

# Colors & Formatting
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
PURPLE="\033[0;35m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
DIM="\033[2m"
RESET="\033[0m"

echo -e "${PURPLE}${BOLD}"
echo "   ____          _      ____       _     _            "
echo "  / ___|___   __| | ___| __ ) _ __(_) __| | __ _  ___ "
echo " | |   / _ \ / _\` |/ _ \  _ \| '__| |/ _\` |/ _\` |/ _ \\"
echo " | |__| (_) | (_| |  __/ |_) | |  | | (_| | (_| |  __/"
echo "  \____\___/ \__,_|\___|____/|_|  |_|\__,_|\__, |\___|"
echo "                                           |___/      "
echo -e "${RESET}"
echo -e "${CYAN}${BOLD} CodeBridge V1 — Local Codebase Analyzer by Vanaila${RESET}"
echo -e "${BOLD} System Environment Verification & Startup${RESET}"
echo "----------------------------------------------------------------"

# 1. Check Python
echo -ne "${BLUE}[1/5] Checking Python 3...${RESET} "
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}${BOLD}FAILED${RESET}"
    echo -e "${RED}Error: Python 3 is required but not found in PATH.${RESET}"
    exit 1
fi
PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
echo -e "${GREEN}✓ Found Python $PY_VERSION${RESET}"

# 2. Check Node & NPM
echo -ne "${BLUE}[2/5] Checking Node.js and npm...${RESET} "
if ! command -v node &>/dev/null || ! command -v npm &>/dev/null; then
    echo -e "${RED}${BOLD}FAILED${RESET}"
    echo -e "${RED}Error: Node.js and npm are required. Please install Node 18+ to proceed.${RESET}"
    exit 1
fi
NODE_VERSION=$(node -v)
NPM_VERSION=$(npm -v)
echo -e "${GREEN}✓ Found Node $NODE_VERSION & npm v$NPM_VERSION${RESET}"

# 3. Check / Configure Virtual Environment & Dependencies
echo -ne "${BLUE}[3/5] Checking backend dependencies...${RESET} "
if [ ! -d "backend/.venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Initializing backend/.venv...${RESET}"
    python3 -m venv backend/.venv
    backend/.venv/bin/pip install --upgrade pip -q
    backend/.venv/bin/pip install -r backend/requirements.txt -q
    echo -e "${GREEN}✓ Virtual environment created & dependencies installed.${RESET}"
else
    echo -e "${GREEN}✓ Virtual environment ready (backend/.venv)${RESET}"
fi

echo -ne "${BLUE}      Checking frontend dependencies...${RESET} "
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Frontend dependencies not found. Installing via npm...${RESET}"
    npm --prefix frontend install
    echo -e "${GREEN}✓ Frontend dependencies installed.${RESET}"
else
    echo -e "${GREEN}✓ Frontend dependencies ready${RESET}"
fi

# 4. Check & Manage Ollama
echo -ne "${BLUE}[4/5] Checking Ollama Local AI Engine...${RESET} "
OLLAMA_STARTED_BY_SCRIPT=false

if command -v ollama &>/dev/null; then
    OLLAMA_BIN=$(command -v ollama)
    # Check if Ollama service is already responding
    if curl -s --max-time 1.5 http://127.0.0.1:11434/api/version &>/dev/null; then
        OLLAMA_VER=$(curl -s http://127.0.0.1:11434/api/version | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', 'unknown'))" 2>/dev/null || echo "active")
        echo -e "${GREEN}✓ Active & reachable on http://127.0.0.1:11434 (v$OLLAMA_VER)${RESET}"
    else
        echo -e "${YELLOW}Installed at $OLLAMA_BIN, but not running.${RESET}"
        echo -ne "      ${CYAN}Starting 'ollama serve' in background...${RESET} "
        ollama serve > "$SCRIPT_DIR/.logs/ollama.log" 2>&1 &
        OLLAMA_PID=$!
        OLLAMA_STARTED_BY_SCRIPT=true

        # Wait up to 5 seconds for Ollama to become active
        READY=false
        for i in {1..10}; do
            sleep 0.5
            if curl -s --max-time 1 http://127.0.0.1:11434/api/version &>/dev/null; then
                READY=true
                break
            fi
        done

        if [ "$READY" = true ]; then
            echo -e "${GREEN}✓ Ollama daemon started (PID: $OLLAMA_PID)${RESET}"
        else
            echo -e "${YELLOW}⚠ Ollama started (PID: $OLLAMA_PID), continuing startup...${RESET}"
        fi
    fi

    # Display installed models if any
    MODELS=$(curl -s --max-time 2 http://127.0.0.1:11434/api/tags 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    models = [m['name'] for m in data.get('models', [])]
    if models:
        print(', '.join(models))
    else:
        print('None downloaded yet (run: ollama run llama3.2)')
except:
    print('None')
" 2>/dev/null || echo "None")
    echo -e "      ${PURPLE}Local Models:${RESET} ${MODELS}"
else
    echo -e "${YELLOW}Not installed (Optional for local models; cloud providers work directly)${RESET}"
    echo -e "      ${PURPLE}Tip:${RESET} Install from https://ollama.com to enable 100% offline private inference."
fi

# 5. Check Ports & Clean Previous Stale Instances (LISTEN only)
echo -ne "${BLUE}[5/5] Verifying ports (8000 & 5173)...${RESET} "

# Check port 8000 (Backend)
PID_8000=$(lsof -iTCP:8000 -sTCP:LISTEN -t 2>/dev/null || true)
if [ -n "$PID_8000" ]; then
    echo -e "${YELLOW}Port 8000 in use by PID $PID_8000. Releasing...${RESET}"
    kill -9 $PID_8000 2>/dev/null || true
    sleep 0.5
fi

# Check port 5173 (Frontend Vite)
PID_5173=$(lsof -iTCP:5173 -sTCP:LISTEN -t 2>/dev/null || true)
if [ -n "$PID_5173" ]; then
    echo -e "${YELLOW}Port 5173 in use by PID $PID_5173. Releasing...${RESET}"
    kill -9 $PID_5173 2>/dev/null || true
    sleep 0.5
fi
echo -e "${GREEN}✓ Ports 8000 & 5173 ready${RESET}"

echo "----------------------------------------------------------------"
echo -e "${GREEN}${BOLD} All checks passed! Starting CodeBridge V1...${RESET}"
echo "----------------------------------------------------------------"

# Process cleanup trap
cleanup() {
    echo ""
    echo -e "${YELLOW}${BOLD} Shutting down CodeBridge services...${RESET}"
    
    if [ -n "$FRONTEND_PID" ]; then
        kill -TERM "$FRONTEND_PID" 2>/dev/null || true
    fi
    if [ -n "$BACKEND_PID" ]; then
        kill -TERM "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ "$OLLAMA_STARTED_BY_SCRIPT" = true ] && [ -n "$OLLAMA_PID" ]; then
        echo -e "${YELLOW} Stopping script-launched Ollama daemon (PID: $OLLAMA_PID)...${RESET}"
        kill -TERM "$OLLAMA_PID" 2>/dev/null || true
    fi

    sleep 0.5
    echo -e "${GREEN}✓ CodeBridge services stopped cleanly. Goodbye!${RESET}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Start Backend
export PYTHONPATH="$SCRIPT_DIR"
backend/.venv/bin/python backend/run.py > "$SCRIPT_DIR/.logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo -e " ${PURPLE}●${RESET} Backend API server started      ${CYAN}http://127.0.0.1:8000${RESET} (PID: $BACKEND_PID)"

# Wait for backend health
BACKEND_READY=false
for i in {1..20}; do
    if curl -s http://127.0.0.1:8000/api/health &>/dev/null; then
        BACKEND_READY=true
        break
    fi
    sleep 0.25
done

if [ "$BACKEND_READY" = false ]; then
    echo -e "${RED} Backend failed to start. Check logs at .logs/backend.log:${RESET}"
    tail -n 20 "$SCRIPT_DIR/.logs/backend.log"
    exit 1
fi

# Start Frontend
npm --prefix frontend run dev > "$SCRIPT_DIR/.logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo -e " ${PURPLE}●${RESET} Frontend Studio started         ${CYAN}http://localhost:5173${RESET} (PID: $FRONTEND_PID)"

echo "----------------------------------------------------------------"
echo -e "${GREEN}${BOLD}🚀 CodeBridge Studio is Live and Ready!${RESET}"
echo ""
echo -e "   🌐 Web Application:   ${BOLD}${CYAN}http://localhost:5173${RESET}"
echo -e "   🔌 REST API:          ${BOLD}http://127.0.0.1:8000${RESET}"
echo -e "   📖 Interactive Docs:  ${BOLD}http://127.0.0.1:8000/docs${RESET}"
echo -e "   🧠 Ollama AI Engine:  ${BOLD}http://127.0.0.1:11434${RESET}"
echo -e "   📄 Logs directory:    ${DIM}.logs/ (backend.log, frontend.log)${RESET}"
echo ""
echo -e "${BOLD}Press [Ctrl+C] to stop all services.${RESET}"
echo "----------------------------------------------------------------"

# Keep script running while both processes are active
while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do
    sleep 1
done

wait

#!/bin/bash

echo "🛑 Stopping Blockchain Security Platform Services..."
echo "================================================="

# Function to check if process exists and kill it
kill_process() {
    local process_name="$1"
    local description="$2"
    
    pids=$(pgrep -f "$process_name" 2>/dev/null)
    if [ -n "$pids" ]; then
        echo "📦 Stopping $description..."
        echo "$pids" | xargs kill -TERM 2>/dev/null
        sleep 2
        
        # Force kill if still running
        remaining_pids=$(pgrep -f "$process_name" 2>/dev/null)
        if [ -n "$remaining_pids" ]; then
            echo "🔨 Force stopping $description..."
            echo "$remaining_pids" | xargs kill -9 2>/dev/null
        fi
        echo "✅ $description stopped"
    else
        echo "ℹ️  $description not running"
    fi
}

# Stop Frontend (Vite dev server)
kill_process "vite.*--port 5173" "Frontend (Vite)"
kill_process "npm run dev" "Frontend (npm)"

# Stop Backend (FastAPI)
kill_process "uvicorn.*main:app" "Backend (FastAPI)"
kill_process "python.*uvicorn.*main:app" "Backend (Python)"

# Stop Ganache
kill_process "ganache-cli" "Ganache CLI"
kill_process "npm run start-chain" "Ganache (npm)"
kill_process "ganache" "Ganache"

# Check ports and force kill if needed
echo ""
echo "🔍 Checking ports..."

check_and_kill_port() {
    local port="$1"
    local service="$2"
    
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pid" ]; then
        echo "🔨 Force killing process on port $port ($service)"
        kill -9 $pid 2>/dev/null
        echo "✅ Port $port freed"
    else
        echo "✅ Port $port is free ($service)"
    fi
}

check_and_kill_port 5173 "Frontend"
check_and_kill_port 8000 "Backend" 
check_and_kill_port 8545 "Ganache"

echo ""
echo "🎉 All services have been stopped successfully!"
echo "================================================="
echo "Services stopped:"
echo "  • Frontend (Vue + Vite) - Port 5173"
echo "  • Backend (FastAPI) - Port 8000" 
echo "  • Ganache Blockchain - Port 8545"
echo ""
echo "You can now safely close terminal windows or restart services."
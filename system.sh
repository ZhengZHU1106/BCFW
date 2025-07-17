#!/bin/bash

# Blockchain-based Intelligent Security Platform - Unified System Management Script
# Phase 8: Contract-Level Role Separation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Function to show usage
show_usage() {
    echo "🔧 Blockchain-based Intelligent Security Platform - System Management"
    echo ""
    echo "Usage: $0 [start|stop|restart|status]"
    echo ""
    echo "Commands:"
    echo "  start    - Start all services (Ganache, Backend, Frontend)"
    echo "  stop     - Stop all services and clean up"
    echo "  restart  - Stop and then start all services"
    echo "  status   - Check status of all services"
    echo ""
    echo "Phase 8: Contract-Level Role Separation"
    echo "- Operators (operator_0 to operator_4): Create proposals"
    echo "- Managers (manager_0 to manager_2): Sign proposals"
    echo "- Smart contract enforces role boundaries"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    local port=$1
    if command_exists lsof; then
        lsof -ti:$port > /dev/null 2>&1
    else
        netstat -an 2>/dev/null | grep ":$port " > /dev/null
    fi
}

# Function to kill process by PID file
kill_by_pid_file() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            sleep 1
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null
            fi
            echo "✅ $service_name stopped (PID: $pid)"
        else
            echo "⚠️  $service_name was not running"
        fi
        rm -f "$pid_file"
    fi
}

# Function to start the system
start_system() {
    echo "🚀 Starting Blockchain-based Intelligent Security Platform..."
    echo "📋 Phase 8: Contract-Level Role Separation"
    echo ""

    # Check if required commands exist
    for cmd in ganache python3 node npm; do
        if ! command_exists "$cmd"; then
            echo "❌ $cmd not found. Please install it first."
            exit 1
        fi
    done

    # Stop any existing services first
    echo "🧹 Cleaning up any existing services..."
    stop_system_quiet

    # Step 1: Start Ganache blockchain
    echo "🔗 Starting Ganache local blockchain..."
    ganache --mnemonic "bulk tonight audit hover toddler orange boost twenty biology flower govern soldier" \
            --blockTime 5 \
            --host 127.0.0.1 \
            --port 8545 \
            --accounts 10 \
            --defaultBalanceEther 1000 > ganache.log 2>&1 &

    GANACHE_PID=$!
    echo "$GANACHE_PID" > .ganache.pid
    echo "✅ Ganache started (PID: $GANACHE_PID)"

    # Wait for Ganache to initialize
    sleep 5

    # Step 2: Deploy MultiSig contract
    echo "📝 Deploying MultiSig contract..."
    if node scripts/deploy_multisig_simple.js; then
        echo "✅ MultiSig contract deployed successfully"
    else
        echo "❌ Failed to deploy MultiSig contract"
        stop_system_quiet
        exit 1
    fi

    # Step 3: Start backend service
    echo "🐍 Starting FastAPI backend..."
    python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
    BACKEND_PID=$!
    echo "$BACKEND_PID" > .backend.pid
    echo "✅ Backend started (PID: $BACKEND_PID)"

    # Step 4: Start frontend service
    echo "🌐 Starting Vue.js frontend..."
    cd frontend
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "$FRONTEND_PID" > ../.frontend.pid
    cd ..
    echo "✅ Frontend started (PID: $FRONTEND_PID)"

    # Wait for services to initialize
    sleep 5

    # Step 5: Verify system status
    echo ""
    echo "🔍 Verifying system status..."
    check_status

    echo ""
    echo "🎉 System startup complete!"
    echo "📊 Access URLs:"
    echo "   - Frontend: http://localhost:5173"
    echo "   - Backend API: http://localhost:8000"
    echo "   - API Documentation: http://localhost:8000/docs"
    echo "   - Ganache RPC: http://127.0.0.1:8545"
    echo ""
    echo "🛑 To stop the system, run: $0 stop"
}

# Function to stop the system (quiet version for internal use)
stop_system_quiet() {
    # Stop services using PID files
    kill_by_pid_file ".frontend.pid" "Frontend"
    kill_by_pid_file ".backend.pid" "Backend"
    kill_by_pid_file ".ganache.pid" "Ganache"

    # Force kill any remaining processes
    processes_to_kill=("uvicorn" "vite" "ganache" "node.*ganache" "python.*uvicorn" "npm.*dev")
    for process in "${processes_to_kill[@]}"; do
        if pgrep -f "$process" > /dev/null; then
            pkill -f "$process" 2>/dev/null
            sleep 1
            if pgrep -f "$process" > /dev/null; then
                pkill -9 -f "$process" 2>/dev/null
            fi
        fi
    done

    # Kill by port
    ports_to_free=(8545 8000 5173 3000 4000 5000 8080 8888)
    for port in "${ports_to_free[@]}"; do
        if command_exists lsof && lsof -ti:$port > /dev/null 2>&1; then
            lsof -ti:$port | xargs kill -9 2>/dev/null
        fi
    done

    # Clean up files
    rm -f ganache.log backend.log frontend.log *.log
    rm -f .ganache.pid .backend.pid .frontend.pid .*.pid
}

# Function to stop the system (with output)
stop_system() {
    echo "🛑 Stopping Blockchain-based Intelligent Security Platform..."
    echo ""

    stop_system_quiet

    sleep 2

    echo ""
    echo "🎉 System shutdown complete!"
    echo "📋 All services have been stopped and cleaned up."

    # Final verification
    echo ""
    echo "🔍 Final verification:"
    if command_exists lsof; then
        for port in 8545 8000 5173; do
            if lsof -ti:$port > /dev/null 2>&1; then
                echo "⚠️  Warning: Port $port is still in use"
            else
                echo "✅ Port $port is free"
            fi
        done
    else
        echo "⚠️  Cannot verify port status (lsof not available)"
    fi
}

# Function to check system status
check_status() {
    echo "🔍 System Status Check:"
    echo ""

    # Check Ganache
    if port_in_use 8545; then
        if curl -s http://127.0.0.1:8545 -X POST -H "Content-Type: application/json" \
           -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}' | grep -q "1337"; then
            echo "✅ Ganache blockchain: Running (Port 8545)"
        else
            echo "⚠️  Ganache blockchain: Port occupied but not responding correctly"
        fi
    else
        echo "❌ Ganache blockchain: Not running"
    fi

    # Check Backend
    if port_in_use 8000; then
        if curl -s http://localhost:8000/health 2>/dev/null | grep -q "healthy"; then
            echo "✅ Backend API: Running (Port 8000)"
        else
            echo "⚠️  Backend API: Port occupied but not responding correctly"
        fi
    else
        echo "❌ Backend API: Not running"
    fi

    # Check Frontend
    if port_in_use 5173; then
        if curl -s http://localhost:5173 2>/dev/null | grep -q "vite"; then
            echo "✅ Frontend: Running (Port 5173)"
        else
            echo "⚠️  Frontend: Port occupied but not responding correctly"
        fi
    else
        echo "❌ Frontend: Not running"
    fi

    echo ""
    echo "📊 Access URLs (if running):"
    echo "   - Frontend: http://localhost:5173"
    echo "   - Backend API: http://localhost:8000"
    echo "   - API Documentation: http://localhost:8000/docs"
    echo "   - Ganache RPC: http://127.0.0.1:8545"
}

# Function to restart the system
restart_system() {
    echo "🔄 Restarting Blockchain-based Intelligent Security Platform..."
    echo ""
    
    stop_system_quiet
    sleep 3
    start_system
}

# Main script logic
case "$1" in
    start)
        start_system
        ;;
    stop)
        stop_system
        ;;
    restart)
        restart_system
        ;;
    status)
        check_status
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
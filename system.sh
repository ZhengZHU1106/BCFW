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
    echo "  start    - Start all services (DevLeChain, Backend, Frontend)"
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
    for cmd in python3 npm; do
        if ! command_exists "$cmd"; then
            echo "❌ $cmd not found. Please install it first."
            exit 1
        fi
    done

    # Check if DevLeChain geth exists
    if [ ! -f "/home/devlechain/Applications/Ethereum/geth" ]; then
        echo "❌ DevLeChain geth not found at /home/devlechain/Applications/Ethereum/geth"
        exit 1
    fi

    # Stop any existing services first
    echo "🧹 Cleaning up any existing services..."
    stop_system_quiet

    # Step 1: Start DevLeChain blockchain
    echo "🔗 Starting DevLeChain blockchain..."
    /home/devlechain/Applications/Ethereum/geth \
        --datadir /home/devlechain/ChainData/20000_20000_ethash_0 \
        --networkid 20000 \
        --http --http.addr 0.0.0.0 --http.port 8545 \
        --http.api "eth,net,web3,personal,miner" \
        --allow-insecure-unlock \
        --nodiscover --maxpeers 0 \
        --mine --miner.threads 1 > devlechain.log 2>&1 &

    DEVLECHAIN_PID=$!
    echo "$DEVLECHAIN_PID" > .devlechain.pid
    echo "✅ DevLeChain started (PID: $DEVLECHAIN_PID)"

    # Wait for DevLeChain to initialize
    echo "⏳ Waiting for DevLeChain to initialize..."
    sleep 10

    # Verify DevLeChain is running
    if ! curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
         -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' 2>/dev/null | grep -q '"result"'; then
        echo "❌ DevLeChain failed to start properly"
        stop_system_quiet
        exit 1
    fi
    echo "✅ DevLeChain blockchain is running"

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
    echo "   - DevLeChain RPC: http://127.0.0.1:8545"
    echo ""
    echo "🛑 To stop the system, run: $0 stop"
}

# Function to stop the system (quiet version for internal use)
stop_system_quiet() {
    # Stop services using PID files
    kill_by_pid_file ".frontend.pid" "Frontend"
    kill_by_pid_file ".backend.pid" "Backend"
    kill_by_pid_file ".devlechain.pid" "DevLeChain"

    # Wait a bit for graceful shutdown
    sleep 2

    # Force kill any remaining processes - more aggressive approach
    processes_to_kill=("uvicorn" "vite" "geth" "python.*uvicorn" "npm.*dev")
    for process in "${processes_to_kill[@]}"; do
        if pgrep -f "$process" > /dev/null; then
            pkill -f "$process" 2>/dev/null
            sleep 2
            if pgrep -f "$process" > /dev/null; then
                pkill -9 -f "$process" 2>/dev/null
            fi
        fi
    done

    # Kill by port - more thorough approach
    ports_to_free=(8545 8000 5173 3000 4000 5000 8080 8888)
    for port in "${ports_to_free[@]}"; do
        # Use lsof to kill processes using specific ports
        if command_exists lsof; then
            # Get all PIDs using the port
            local pids=$(lsof -ti:$port 2>/dev/null)
            if [ ! -z "$pids" ]; then
                echo "$pids" | xargs kill -9 2>/dev/null
            fi
        fi
    done

    # Additional wait for port release
    sleep 3

    # Verify critical ports are free
    for port in 8545 8000 5173; do
        if command_exists lsof && lsof -ti:$port > /dev/null 2>&1; then
            echo "⚠️  Warning: Port $port still in use, attempting final cleanup..."
            lsof -ti:$port | xargs kill -9 2>/dev/null
            sleep 1
        fi
    done

    # Clean up files
    rm -f devlechain.log backend.log frontend.log *.log
    rm -f .devlechain.pid .backend.pid .frontend.pid .*.pid
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

    # Check DevLeChain
    if port_in_use 8545; then
        if curl -s -m 5 http://127.0.0.1:8545 -X POST -H "Content-Type: application/json" \
           -d '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}' 2>/dev/null | grep -q '"result"'; then
            echo "✅ DevLeChain blockchain: Running (Port 8545)"
        else
            echo "⚠️  DevLeChain blockchain: Port occupied but not responding correctly"
        fi
    else
        echo "❌ DevLeChain blockchain: Not running"
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
    echo "   - DevLeChain RPC: http://127.0.0.1:8545"
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
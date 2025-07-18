#!/bin/bash
# BlueFusion Service Manager

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    
    if lsof -i:$port > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name is running on port $port${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name is not running${NC}"
        return 1
    fi
}

# Function to start API server
start_api() {
    echo -e "${YELLOW}Starting API server...${NC}"
    cd "$(dirname "$0")"
    python src/api/api_server.py &
    API_PID=$!
    sleep 3
    
    if check_service "API server" 8000; then
        echo -e "${GREEN}API server started successfully (PID: $API_PID)${NC}"
    else
        echo -e "${RED}Failed to start API server${NC}"
        return 1
    fi
}

# Function to start UI
start_ui() {
    echo -e "${YELLOW}Starting UI...${NC}"
    cd "$(dirname "$0")"
    python src/ui/gradio_interface.py &
    UI_PID=$!
    sleep 3
    
    if check_service "UI" 7860; then
        echo -e "${GREEN}UI started successfully (PID: $UI_PID)${NC}"
        echo -e "${GREEN}Access the UI at: http://localhost:7860${NC}"
    else
        echo -e "${RED}Failed to start UI${NC}"
        return 1
    fi
}

# Function to stop services
stop_services() {
    echo -e "${YELLOW}Stopping services...${NC}"
    
    # Kill API server
    API_PIDS=$(lsof -ti:8000)
    if [ ! -z "$API_PIDS" ]; then
        kill $API_PIDS
        echo -e "${GREEN}API server stopped${NC}"
    fi
    
    # Kill UI
    UI_PIDS=$(lsof -ti:7860)
    if [ ! -z "$UI_PIDS" ]; then
        kill $UI_PIDS
        echo -e "${GREEN}UI stopped${NC}"
    fi
}

# Main menu
case "$1" in
    start)
        echo -e "${YELLOW}Starting BlueFusion services...${NC}"
        
        # Check current status
        check_service "API server" 8000
        API_RUNNING=$?
        
        check_service "UI" 7860
        UI_RUNNING=$?
        
        # Start services if not running
        if [ $API_RUNNING -ne 0 ]; then
            start_api
        fi
        
        if [ $UI_RUNNING -ne 0 ]; then
            start_ui
        fi
        
        echo -e "\n${GREEN}BlueFusion is ready!${NC}"
        echo -e "API: http://localhost:8000/docs"
        echo -e "UI: http://localhost:7860"
        ;;
        
    stop)
        stop_services
        ;;
        
    restart)
        stop_services
        sleep 2
        $0 start
        ;;
        
    status)
        echo -e "${YELLOW}BlueFusion Service Status:${NC}"
        check_service "API server" 8000
        check_service "UI" 7860
        ;;
        
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Commands:"
        echo "  start   - Start both API and UI services"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  status  - Check service status"
        exit 1
        ;;
esac
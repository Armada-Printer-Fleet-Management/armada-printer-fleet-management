#!/bin/bash
# ═════════════════════════════════════════════════════════════════════════════════════════════════
# Armada Stack Launcher
#
# Launches the complete Armada development stack (server, web, Postgres, Garage, Keycloak)
# in a single command with helpful output and status information.
#
# Usage:
#   ./armada-stack.sh [start|stop|status|logs]
#
# Commands:
#   start   - Start the development stack (default if no command specified)
#   stop    - Stop the development stack
#   status  - Show the status of all containers
#   logs    - Show real-time logs from all services
#
# Examples:
#   ./armada-stack.sh              # Start the stack
#   ./armada-stack.sh stop         # Stop the stack
#   ./armada-stack.sh status       # Check status
#   ./armada-stack.sh logs         # Follow logs
# ═════════════════════════════════════════════════════════════════════════════════════════════════

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if we're in the Armada repo
if [ ! -f "$SCRIPT_DIR/scripts/compose_run.py" ]; then
    echo -e "${RED}Error: This script must be run from the Armada repository root${NC}"
    exit 1
fi

# Default command
COMMAND="${1:-start}"

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────────────────────────

print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

print_service_info() {
    local service=$1
    local port=$2
    local url=$3
    printf "  %-20s Port %-6s ${CYAN}%s${NC}\n" "$service" "$port" "$url"
}

wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0

    print_info "Waiting for $name to be ready..."

    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            print_success "$name is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        printf "."
        sleep 1
    done

    echo ""
    print_warning "$name is taking longer than expected, but stack may still be starting..."
    return 1
}

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────────────────────────

start_stack() {
    print_header "Starting Armada Development Stack"

    print_info "Launching services with Docker Compose..."
    echo ""

    # Start the stack
    python "$SCRIPT_DIR/scripts/compose_run.py" dev up
}

stop_stack() {
    print_header "Stopping Armada Development Stack"

    print_info "Stopping all services..."
    python "$SCRIPT_DIR/scripts/compose_run.py" dev down

    echo ""
    print_success "Stack stopped"
}

show_status() {
    print_header "Armada Stack Status"

    # Load env file for docker compose
    if [ ! -f "$SCRIPT_DIR/config/compose.dev.env" ]; then
        print_error "Environment file not found. Start the stack first with './armada-stack.sh start'"
        exit 1
    fi

    echo ""
    docker compose -f "$SCRIPT_DIR/infra/dev/compose.yaml" \
        --env-file "$SCRIPT_DIR/config/compose.dev.env" ps

    echo ""
    print_header "Service URLs"
    echo ""
    print_service_info "Web App" "5174" "http://localhost:5174"
    print_service_info "Server API" "8000" "http://localhost:8000"
    print_service_info "Keycloak" "8080" "http://localhost:8080"
    print_service_info "Postgres" "5432" "localhost:5432"
    print_service_info "Garage (S3)" "3900" "http://localhost:3900"
    echo ""
}

show_logs() {
    print_header "Armada Stack Logs (Ctrl+C to exit)"

    if [ ! -f "$SCRIPT_DIR/config/compose.dev.env" ]; then
        print_error "Environment file not found. Start the stack first with './armada-stack.sh start'"
        exit 1
    fi

    echo ""
    docker compose -f "$SCRIPT_DIR/infra/dev/compose.yaml" \
        --env-file "$SCRIPT_DIR/config/compose.dev.env" logs -f
}

show_help() {
    echo "Armada Stack Launcher"
    echo ""
    echo "Usage: $(basename "$0") [command]"
    echo ""
    echo "Commands:"
    echo "  start       Start the development stack (default)"
    echo "  stop        Stop the development stack"
    echo "  status      Show container status and service URLs"
    echo "  logs        Follow real-time logs from all services"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $(basename "$0")              # Start the stack"
    echo "  $(basename "$0") stop         # Stop the stack"
    echo "  $(basename "$0") status       # Check status"
}

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────────────────────────

case "$COMMAND" in
    start)
        start_stack
        ;;
    stop)
        stop_stack
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac

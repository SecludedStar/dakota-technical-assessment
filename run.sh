#!/bin/bash
set -e

# Dakota Analytics Technical Assessment - Run Script
# This script sets up and runs the complete data pipeline

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check for required tools
check_requirements() {
    log_info "Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_success "All requirements met."
}

# Setup environment
setup_env() {
    log_info "Setting up environment..."

    if [ ! -f .env ]; then
        log_warn ".env file not found. Creating default .env..."
        cat > .env << 'ENVFILE'
# Dakota Analytics Environment Configuration
POSTGRES_USER=dakota
POSTGRES_PASSWORD=dakota_dev
POSTGRES_DB=dakota_analytics
POSTGRES_PORT=5432

# EIA API Key - Get yours at https://www.eia.gov/opendata/register.php
# Note: 'demo_key' works for basic testing but has rate limits
EIA_API_KEY=demo_key

# Service Ports
API_PORT=8000
DAGSTER_PORT=3000
ENVFILE
        log_warn "Created .env with defaults. For full EIA data, update EIA_API_KEY."
    fi

    source .env
    log_success "Environment configured."
}

# Build and start services
start_services() {
    log_info "Building and starting services..."
    
    # Use docker compose (v2) if available, otherwise docker-compose (v1)
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    $COMPOSE_CMD build --parallel
    $COMPOSE_CMD up -d
    
    log_info "Waiting for services to be healthy..."
    sleep 10
    
    # Wait for PostgreSQL
    log_info "Waiting for PostgreSQL..."
    for i in {1..30}; do
        if $COMPOSE_CMD exec -T postgres pg_isready -U ${POSTGRES_USER:-dakota} -d ${POSTGRES_DB:-dakota_analytics} &> /dev/null; then
            log_success "PostgreSQL is ready."
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "PostgreSQL failed to start within 30 seconds."
            exit 1
        fi
        sleep 1
    done
    
    # Wait for API
    log_info "Waiting for Enrichment API..."
    for i in {1..30}; do
        if curl -s http://localhost:${API_PORT:-8000}/health &> /dev/null; then
            log_success "Enrichment API is ready."
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "API failed to start within 30 seconds."
            exit 1
        fi
        sleep 1
    done
    
    log_success "All services are running."
}

# Run the data pipeline
run_pipeline() {
    log_info "Running data pipeline..."
    
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    # Trigger the daily batch job via Dagster
    log_info "Triggering daily batch pipeline..."
    $COMPOSE_CMD exec -T dagster-webserver dagster job execute -j full_pipeline -m orchestration
    
    log_success "Pipeline execution complete."
}

# Run dbt transformations
run_dbt() {
    log_info "Running dbt transformations..."

    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi

    log_info "Installing dbt dependencies..."
    $COMPOSE_CMD exec -T dagster-webserver bash -c "cd /opt/dagster/app/dbt && dbt deps --profiles-dir ."

    log_info "Running dbt models..."
    $COMPOSE_CMD exec -T dagster-webserver bash -c "cd /opt/dagster/app/dbt && dbt run --profiles-dir . --target dev"

    log_info "Running dbt tests..."
    $COMPOSE_CMD exec -T dagster-webserver bash -c "cd /opt/dagster/app/dbt && dbt test --profiles-dir . --target dev"

    log_success "dbt transformations complete."
}

# Generate reports
generate_reports() {
    log_info "Generating reports..."

    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi

    # Run reports via Dagster job for proper orchestration
    log_info "Triggering reports job..."
    $COMPOSE_CMD exec -T dagster-webserver dagster job execute -j reports_generation -m orchestration

    log_success "Reports generated in reports/output/"
}

# Show status
show_status() {
    log_info "Service Status:"
    
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    $COMPOSE_CMD ps
    
    echo ""
    log_info "Access Points:"
    echo "  - Dagster UI:      http://localhost:${DAGSTER_PORT:-3000}"
    echo "  - Enrichment API:  http://localhost:${API_PORT:-8000}"
    echo "  - API Docs:        http://localhost:${API_PORT:-8000}/docs"
    echo "  - PostgreSQL:      localhost:${POSTGRES_PORT:-5432}"
}

# Stop all services
stop_services() {
    log_info "Stopping services..."
    
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    $COMPOSE_CMD down
    log_success "All services stopped."
}

# Clean up everything
clean() {
    log_warn "This will remove all containers, volumes, and data. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        if docker compose version &> /dev/null; then
            COMPOSE_CMD="docker compose"
        else
            COMPOSE_CMD="docker-compose"
        fi
        
        $COMPOSE_CMD down -v --rmi local
        rm -rf reports/output/*.xlsx reports/output/*.pdf reports/output/*.html reports/output/*.ipynb
        log_success "Cleanup complete."
    else
        log_info "Cleanup cancelled."
    fi
}

# Print usage
usage() {
    echo "Dakota Analytics Technical Assessment"
    echo ""
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start      Build and start all services"
    echo "  stop       Stop all services"
    echo "  restart    Restart all services"
    echo "  status     Show service status and access points"
    echo "  pipeline   Run the complete data pipeline"
    echo "  dbt        Run dbt transformations only"
    echo "  reports    Generate reports only"
    echo "  logs       Show service logs"
    echo "  clean      Remove all containers, volumes, and data"
    echo "  help       Show this help message"
    echo ""
    echo "Quick Start:"
    echo "  1. Copy .env.example to .env and add your EIA API key"
    echo "  2. Run: ./run.sh start"
    echo "  3. Run: ./run.sh pipeline"
    echo "  4. View Dagster UI at http://localhost:3000"
}

# Main
case "${1:-help}" in
    start)
        check_requirements
        setup_env
        start_services
        show_status
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        start_services
        show_status
        ;;
    status)
        show_status
        ;;
    pipeline)
        run_pipeline
        ;;
    dbt)
        run_dbt
        ;;
    reports)
        generate_reports
        ;;
    logs)
        if docker compose version &> /dev/null; then
            docker compose logs -f
        else
            docker-compose logs -f
        fi
        ;;
    clean)
        clean
        ;;
    help|*)
        usage
        ;;
esac

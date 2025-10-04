#!/bin/bash
# Quick script to train models using the microservices architecture

set -e

echo "=========================================="
echo "Training Service - Quick Start"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.microservices.yml"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠ docker-compose not found. Please install it first.${NC}"
    exit 1
fi

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -b, --build             Build the training service first"
    echo "  -m, --mode MODE         Training mode: toy, unified, host-specific (default: toy)"
    echo "  -c, --config FILE       Use custom configuration file"
    echo ""
    echo "Examples:"
    echo "  $0 --build --mode toy                    # Build and train with toy dataset"
    echo "  $0 --mode unified                         # Train unified multi-host model"
    echo "  $0 --mode host-specific                   # Train host-specific models"
    echo "  $0 --config data/input/my_config.json     # Use custom config"
    echo ""
}

# Parse arguments
BUILD=false
MODE="toy"
CUSTOM_CONFIG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -c|--config)
            CUSTOM_CONFIG="$2"
            shift 2
            ;;
        *)
            echo -e "${YELLOW}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# Build service if requested
if [ "$BUILD" = true ]; then
    echo -e "${BLUE}📦 Building training service...${NC}"
    docker-compose -f "$COMPOSE_FILE" build training
    echo -e "${GREEN}✓ Build complete${NC}"
    echo ""
fi

# Determine config file
if [ -n "$CUSTOM_CONFIG" ]; then
    CONFIG_FILE="$CUSTOM_CONFIG"
    echo -e "${BLUE}📋 Using custom configuration: $CONFIG_FILE${NC}"
else
    case $MODE in
        toy)
            CONFIG_FILE="data/input/training_toy.json"
            echo -e "${BLUE}📋 Quick test with toy dataset${NC}"
            ;;
        unified)
            CONFIG_FILE="data/input/training_unified.json"
            echo -e "${BLUE}📋 Training unified multi-host model${NC}"
            ;;
        host-specific)
            CONFIG_FILE="data/input/training_host_specific.json"
            echo -e "${BLUE}📋 Training host-specific models${NC}"
            ;;
        *)
            echo -e "${YELLOW}⚠ Unknown mode: $MODE${NC}"
            echo "Valid modes: toy, unified, host-specific"
            exit 1
            ;;
    esac
fi

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}⚠ Configuration file not found: $CONFIG_FILE${NC}"
    exit 1
fi

# Display configuration
echo ""
echo "Configuration:"
echo "  Mode:        $MODE"
echo "  Config File: $CONFIG_FILE"
echo ""

# Start training
echo -e "${BLUE}🚀 Starting training...${NC}"
echo ""

docker-compose -f "$COMPOSE_FILE" run --rm training \
  --input "/data/input/$(basename $CONFIG_FILE)"

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Training completed successfully!${NC}"
    echo ""
    echo "Results:"
    echo "  Models:  ./models/"
    echo "  Logs:    ./data/output/training/"
    echo ""
    echo "View results:"
    echo "  ls -lh models/"
    echo "  cat data/output/training/*_result.json | jq"
else
    echo ""
    echo -e "${YELLOW}⚠ Training failed. Check logs for details.${NC}"
    exit 1
fi

echo "=========================================="
echo "Training Complete!"
echo "=========================================="


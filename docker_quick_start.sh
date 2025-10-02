#!/bin/bash
# Quick start script for Codon Verifier Docker environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Codon Verifier Docker Quick Start ===${NC}\n"

# Check prerequisites
echo "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${NC}"

# Check NVIDIA Docker
if ! docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo -e "${YELLOW}Warning: NVIDIA Docker runtime test failed${NC}"
    echo -e "${YELLOW}Make sure nvidia-docker2 is installed and your GPU drivers are up to date${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ NVIDIA Docker runtime detected${NC}"
fi

echo -e "\n${GREEN}=== Building Docker image ===${NC}"
docker-compose build

echo -e "\n${GREEN}=== Starting container ===${NC}"
docker-compose up -d

echo -e "\n${GREEN}=== Verifying installation ===${NC}"
docker-compose exec -T codon-verifier bash << 'EOF'
echo "Python version:"
python --version

echo -e "\nPyTorch & CUDA:"
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}')"

echo -e "\nEvo2:"
python -c "import evo2; print('Evo2: installed')" 2>&1

echo -e "\nCodonTransformer:"
python -c "from CodonTransformer import DNA2PROTEIN; print('CodonTransformer: installed')" 2>&1

echo -e "\nViennaRNA:"
RNAfold --version 2>&1 | head -n 1

echo -e "\nCodon Verifier framework:"
python -c "from codon_verifier import generator; print('Codon Verifier: loaded')" 2>&1
EOF

echo -e "\n${GREEN}=== Setup Complete! ===${NC}\n"
echo "You can now:"
echo -e "  1. Enter the container:    ${YELLOW}docker-compose exec codon-verifier bash${NC}"
echo -e "  2. Run JupyterLab:         ${YELLOW}docker-compose exec codon-verifier jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root${NC}"
echo -e "  3. Run demo script:        ${YELLOW}docker-compose exec codon-verifier python codon_verifier/run_demo.py${NC}"
echo -e "  4. Stop container:         ${YELLOW}docker-compose down${NC}"
echo -e "\nFor more details, see: ${YELLOW}docs/docker_setup.md${NC}\n"

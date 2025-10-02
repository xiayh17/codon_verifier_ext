#!/bin/bash
# Example workflow for using multi-host UniProt dataset

set -e

echo "=========================================="
echo "Multi-Host Dataset Training Pipeline"
echo "=========================================="

# Configuration
DATA_DIR="./data/2025_bio-os_data/dataset"
OUTPUT_DIR="./outputs/multihost"
CONVERTED_DIR="$OUTPUT_DIR/converted"
MODELS_DIR="$OUTPUT_DIR/models"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$CONVERTED_DIR"
mkdir -p "$MODELS_DIR"

# Step 1: Convert TSV datasets to JSONL
echo ""
echo "Step 1: Converting TSV datasets to JSONL..."
echo "--------------------------------------------"

python -m codon_verifier.data_converter \
    --input "$DATA_DIR" \
    --output "$CONVERTED_DIR" \
    --merge \
    --max-records 10000 \
    --filter-reviewed

echo "✓ Conversion complete"

# Step 2: Train unified multi-host model
echo ""
echo "Step 2: Training unified multi-host model..."
echo "--------------------------------------------"

python -m codon_verifier.train_surrogate_multihost \
    --data "$CONVERTED_DIR/merged_dataset.jsonl" \
    --out "$MODELS_DIR/unified_multihost.pkl" \
    --mode unified \
    --balance-hosts \
    --max-samples 5000

echo "✓ Unified model trained"

# Step 3: Train host-specific models
echo ""
echo "Step 3: Training host-specific models..."
echo "--------------------------------------------"

python -m codon_verifier.train_surrogate_multihost \
    --data "$CONVERTED_DIR/merged_dataset.jsonl" \
    --out "$MODELS_DIR/host_specific" \
    --mode host-specific \
    --hosts E_coli Human Mouse

echo "✓ Host-specific models trained"

# Step 4: Compare models (optional)
echo ""
echo "Step 4: Model comparison..."
echo "--------------------------------------------"

echo "Models trained:"
ls -lh "$MODELS_DIR"/*.pkl "$MODELS_DIR"/host_specific/*.pkl 2>/dev/null || true

echo ""
echo "=========================================="
echo "Pipeline complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Use models for codon optimization:"
echo "     python codon_verifier/generate_demo.py \\"
echo "       --aa MAAAAAAA \\"
echo "       --host E_coli \\"
echo "       --surrogate $MODELS_DIR/unified_multihost.pkl"
echo ""
echo "  2. Evaluate offline:"
echo "     python codon_verifier/evaluate_offline.py \\"
echo "       --dna ATGGCTGCT... \\"
echo "       --model $MODELS_DIR/unified_multihost.pkl"


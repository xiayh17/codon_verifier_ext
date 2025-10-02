# Microservice Architecture Design

## Overview

This project uses a **microservice architecture** where each major tool runs in its own isolated container. Tools communicate via standardized JSON input/output through shared volumes.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     Host Machine                        │
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Evo2      │  │   Codon     │  │   Codon     │     │
│  │  Service    │  │ Transformer │  │  Verifier   │     │
│  │             │  │   Service   │  │   Service   │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │              │
│         └────────────────┴────────────────┘              │
│                          │                               │
│                  ┌───────▼────────┐                      │
│                  │  Shared Data   │                      │
│                  │    Volume      │                      │
│                  │  /data/input   │                      │
│                  │  /data/output  │                      │
│                  └────────────────┘                      │
└─────────────────────────────────────────────────────────┘
```

## Benefits

1. **No Dependency Conflicts**: Each service has its own Python environment
2. **Independent Scaling**: Run multiple instances of any service
3. **Easy Updates**: Update one service without affecting others
4. **Batch Processing**: Process multiple files in parallel
5. **Fault Isolation**: One service failure doesn't crash others

## Data Exchange Format

### Standard Input Format (JSON)
```json
{
  "task": "predict_sequence",
  "input": {
    "sequence": "ATGCGATCG...",
    "organism": "human",
    "parameters": {
      "temperature": 0.8
    }
  },
  "metadata": {
    "request_id": "req_001",
    "timestamp": "2025-10-02T10:30:00Z"
  }
}
```

### Standard Output Format (JSON)
```json
{
  "task": "predict_sequence",
  "status": "success",
  "output": {
    "predicted_sequence": "ATGCGATCG...",
    "confidence_scores": [0.95, 0.88, ...],
    "metrics": {
      "cai": 0.85,
      "gc_content": 0.52
    }
  },
  "metadata": {
    "request_id": "req_001",
    "processing_time_ms": 1250,
    "service": "evo2",
    "version": "1.0.0"
  }
}
```

## Services

### 1. Evo2 Service
- **Purpose**: DNA sequence generation and prediction
- **Base Image**: `nvcr.io/nvidia/pytorch:25.04-py3`
- **Input**: Sequence context, generation parameters
- **Output**: Generated sequences with confidence scores
- **Port**: 8001
- **GPU**: Required

### 2. CodonTransformer Service
- **Purpose**: Codon optimization
- **Base Image**: `python:3.10-slim`
- **Input**: Protein or DNA sequence, target organism
- **Output**: Optimized codon sequence with CAI scores
- **Port**: 8002
- **GPU**: Optional (CPU fallback)

### 3. Codon Verifier Service
- **Purpose**: Sequence verification and analysis
- **Base Image**: `python:3.10-slim`
- **Input**: DNA sequence for verification
- **Output**: Verification results, quality metrics
- **Port**: 8003
- **GPU**: Not required

## Directory Structure

```
codon_verifier_ext/
├── services/
│   ├── evo2/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app.py
│   ├── codon_transformer/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app.py
│   └── codon_verifier/
│       ├── Dockerfile
│       ├── requirements.txt
│       └── app.py
├── data/
│   ├── input/
│   └── output/
├── scripts/
│   ├── batch_process.py
│   └── pipeline.py
├── docker-compose.yml
└── README.md
```

## Usage Patterns

### Pattern 1: Direct File Processing
```bash
# Put input files in data/input/
cp my_sequences.json data/input/

# Run specific service
docker-compose run evo2 python app.py --input /data/input/my_sequences.json

# Results appear in data/output/
```

### Pattern 2: Batch Processing
```bash
# Process multiple files
python scripts/batch_process.py --service evo2 --input-dir data/input/

# Or use pipeline for sequential processing
python scripts/pipeline.py --config pipeline_config.yaml
```

### Pattern 3: REST API (Optional)
```bash
# Start all services
docker-compose up -d

# Send HTTP requests
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d @input.json
```

## Workflow Examples

### Example 1: Complete Pipeline
```bash
# 1. Generate sequences with Evo2
docker-compose run evo2 process --input /data/input/prompts.json

# 2. Optimize codons with CodonTransformer
docker-compose run codon_transformer process --input /data/output/evo2_results.json

# 3. Verify with Codon Verifier
docker-compose run codon_verifier process --input /data/output/optimized_sequences.json
```

### Example 2: Parallel Processing
```bash
# Process 100 sequences in parallel using 10 worker instances
python scripts/batch_process.py \
  --service evo2 \
  --input-dir data/input/batch_001/ \
  --workers 10
```

## Configuration

Each service can be configured via environment variables or config files:

```yaml
# docker-compose.yml
services:
  evo2:
    environment:
      - MODEL_PATH=/models/evo2
      - BATCH_SIZE=32
      - GPU_MEMORY_LIMIT=16GB
```

## Monitoring and Logging

- Logs: `logs/[service_name]/`
- Metrics: Prometheus-compatible metrics at `/metrics` endpoint
- Health checks: `/health` endpoint for each service


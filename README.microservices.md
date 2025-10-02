# Codon Verifier Framework - Microservices Architecture

## 🎯 Overview

This project provides a **microservices-based architecture** for DNA sequence analysis, combining three powerful tools:

1. **Evo2** - DNA sequence generation and prediction
2. **CodonTransformer** - Codon optimization
3. **Codon Verifier** - Sequence verification and analysis

Each tool runs in its **own isolated container**, avoiding dependency conflicts and enabling parallel batch processing.

## ✨ Key Benefits

- ✅ **No Dependency Conflicts** - Each service has its own environment
- ✅ **Easy Batch Processing** - Process hundreds of files in parallel
- ✅ **Fault Isolation** - One service failure doesn't crash others
- ✅ **Independent Scaling** - Run multiple instances of any service
- ✅ **Simple Updates** - Update services independently

## 📁 Project Structure

```
codon_verifier_ext/
├── services/
│   ├── evo2/                    # Evo2 service
│   │   ├── Dockerfile
│   │   ├── app.py
│   │   └── utils.py
│   ├── codon_transformer/       # CodonTransformer service
│   │   ├── Dockerfile
│   │   ├── app.py
│   │   └── utils.py
│   └── codon_verifier/          # Codon Verifier service
│       ├── Dockerfile
│       ├── app.py
│       └── utils.py
├── data/
│   ├── input/                   # Put your input JSON files here
│   └── output/                  # Results appear here
├── scripts/
│   ├── batch_process.py         # Parallel batch processing
│   └── pipeline.py              # Sequential pipeline
├── docker-compose.microservices.yml
├── ARCHITECTURE.md              # Detailed architecture docs
└── README.microservices.md      # This file
```

## 🚀 Quick Start

### Step 1: Build All Services

```bash
# Build all service images
docker-compose -f docker-compose.microservices.yml build
```

### Step 2: Prepare Input Data

Create a JSON file in `data/input/`:

```json
{
  "task": "generate_sequence",
  "input": {
    "sequence": "ATGCGATCGATCGATCG",
    "organism": "human",
    "parameters": {
      "temperature": 0.8
    }
  },
  "metadata": {
    "request_id": "task_001",
    "timestamp": "2025-10-02T10:30:00Z"
  }
}
```

### Step 3: Run a Service

```bash
# Run Evo2 on your input file
docker-compose -f docker-compose.microservices.yml run --rm evo2 \
  --input /data/input/your_task.json

# Results will be in data/output/evo2/your_task_result.json
```

## 💡 Usage Examples

### Example 1: Single File Processing

```bash
# Generate sequences with Evo2
docker-compose -f docker-compose.microservices.yml run --rm evo2 \
  --input /data/input/sequences.json

# Optimize codons
docker-compose -f docker-compose.microservices.yml run --rm codon_transformer \
  --input /data/output/evo2/sequences_result.json

# Verify results
docker-compose -f docker-compose.microservices.yml run --rm codon_verifier \
  --input /data/output/codon_transformer/sequences_result_result.json
```

### Example 2: Batch Processing (Parallel)

Process 100 files using 10 parallel workers:

```bash
# First, build the services
docker-compose -f docker-compose.microservices.yml build

# Run batch processing
python scripts/batch_process.py \
  --service evo2 \
  --input-dir data/input/ \
  --workers 10
```

Output:
```
2025-10-02 10:30:15 - INFO - Found 100 files to process
2025-10-02 10:30:15 - INFO - Using 10 parallel workers
2025-10-02 10:30:18 - INFO - ✓ task_001.json completed in 2.43s
2025-10-02 10:30:19 - INFO - ✓ task_002.json completed in 3.12s
...
============================================================
BATCH PROCESSING SUMMARY
============================================================
Total files:     100
Successful:      98
Failed/Timeout:  2
Average time:    2.87s
============================================================
```

### Example 3: Sequential Pipeline

Run complete pipeline (Evo2 → CodonTransformer → CodonVerifier):

```bash
python scripts/pipeline.py \
  --input data/input/my_sequence.json \
  --data-dir data/
```

### Example 4: Batch Different Organisms

Create multiple input files for different organisms:

```bash
# Create batch input files
for organism in human mouse ecoli yeast; do
  echo "{
    \"task\": \"optimize\",
    \"input\": {
      \"sequence\": \"ATGAAACGTTTG...\",
      \"organism\": \"${organism}\"
    },
    \"metadata\": {\"request_id\": \"${organism}_001\"}
  }" > data/input/${organism}_task.json
done

# Process all at once
python scripts/batch_process.py \
  --service codon_transformer \
  --input-dir data/input/ \
  --workers 4
```

## 📊 Data Format Specifications

### Input Format (JSON)

```json
{
  "task": "task_name",           // e.g., "generate", "optimize", "verify"
  "input": {
    "sequence": "ATGC...",       // DNA sequence
    "organism": "human",         // Target organism (optional)
    "parameters": {              // Task-specific parameters
      "temperature": 0.8,
      "max_length": 500
    }
  },
  "metadata": {
    "request_id": "unique_id",   // For tracking
    "timestamp": "ISO8601",      // Optional
    "description": "..."         // Optional
  }
}
```

### Output Format (JSON)

```json
{
  "task": "task_name",
  "status": "success",           // or "error"
  "output": {
    "result_sequence": "ATGC...",
    "confidence_scores": [0.95, 0.88, ...],
    "metrics": {
      "cai": 0.85,
      "gc_content": 0.52
    }
  },
  "metadata": {
    "request_id": "unique_id",
    "processing_time_ms": 1250,
    "service": "evo2",
    "version": "1.0.0"
  }
}
```

## 🔧 Advanced Usage

### Running Services Independently

```bash
# Build specific service
docker build -t my-evo2 services/evo2/

# Run with custom volumes
docker run --gpus all --rm \
  -v $(pwd)/data:/data \
  my-evo2 --input /data/input/task.json
```

### Scaling Up

```bash
# Scale CodonTransformer to 5 instances
docker-compose -f docker-compose.microservices.yml up -d --scale codon_transformer=5
```

### Custom Processing Script

```python
import subprocess
import json
from pathlib import Path

def process_with_service(service, input_file):
    cmd = [
        'docker', 'run', '--rm',
        '-v', f'{Path.cwd()}/data:/data',
        f'codon-verifier/{service}:latest',
        '--input', f'/data/input/{input_file}'
    ]
    subprocess.run(cmd, check=True)

# Use in your workflow
process_with_service('evo2', 'my_data.json')
process_with_service('codon_transformer', 'evo2_output.json')
```

## 🐛 Troubleshooting

### Service build fails

```bash
# Check Docker is running
docker info

# Build with verbose output
docker-compose -f docker-compose.microservices.yml build --no-cache --progress=plain
```

### Out of memory

```bash
# Limit Docker memory usage
docker-compose -f docker-compose.microservices.yml run --rm \
  --memory="8g" \
  evo2 --input /data/input/task.json
```

### Permission errors with data directory

```bash
# Fix permissions
chmod -R 755 data/
chown -R $USER:$USER data/
```

## 📝 Configuration

### Environment Variables

Each service can be configured via environment variables in `docker-compose.microservices.yml`:

```yaml
services:
  evo2:
    environment:
      - CUDA_VISIBLE_DEVICES=0      # GPU selection
      - HF_HOME=/cache/huggingface  # Cache directory
      - BATCH_SIZE=32               # Batch size
```

### Service-Specific Config

See `ARCHITECTURE.md` for detailed configuration options for each service.

## 🔬 Development

### Adding New Services

1. Create directory: `services/my_service/`
2. Add `Dockerfile`, `app.py`, `utils.py`
3. Update `docker-compose.microservices.yml`
4. Follow the standard input/output JSON format

### Testing Services

```bash
# Test single service
docker-compose -f docker-compose.microservices.yml run --rm evo2 --help

# Run with example data
docker-compose -f docker-compose.microservices.yml run --rm evo2 \
  --input /data/input/example_task.json
```

## 📚 Additional Resources

- **Architecture Details**: See `ARCHITECTURE.md`
- **Original Monolithic Dockerfile**: See `Dockerfile` (legacy)
- **API Documentation**: Each service's `app.py` has built-in help

## 🤝 Contributing

This microservices architecture makes it easy to contribute:

1. Each service is independent
2. Standard JSON interface
3. No dependency conflicts
4. Easy to test in isolation

## 📄 License

See LICENSE file for details.

## 🙋 Support

For issues or questions:
1. Check `ARCHITECTURE.md` for design details
2. Review service logs in `logs/` directory
3. Open an issue with example input/output

---

**Previous Version**: If you need the monolithic (single container) version, it's still available in `Dockerfile`. However, we strongly recommend the microservices approach for production use.


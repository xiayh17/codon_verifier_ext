# 🚀 Quick Start Guide - Microservices Architecture

## What You Get

Three independent services that can work together or separately:
- **Evo2**: DNA sequence generation
- **CodonTransformer**: Codon optimization  
- **CodonVerifier**: Sequence verification

## 3-Minute Setup

### 1. Build Services (5-10 minutes)

```bash
docker-compose -f docker-compose.microservices.yml build
```

### 2. Test with Example Data

```bash
# Test Evo2
docker-compose -f docker-compose.microservices.yml run --rm evo2 \
  --input /data/input/example_task.json

# Check output
ls data/output/evo2/
```

### 3. Process Your Data

Put your JSON files in `data/input/` and run:

```bash
# Single file
docker-compose -f docker-compose.microservices.yml run --rm evo2 \
  --input /data/input/your_file.json

# Batch processing (10 parallel workers)
python scripts/batch_process.py \
  --service evo2 \
  --input-dir data/input/ \
  --workers 10
```

## Input File Format

Save as `data/input/my_task.json`:

```json
{
  "task": "generate_sequence",
  "input": {
    "sequence": "ATGCGATCGATCG",
    "organism": "human",
    "parameters": {
      "temperature": 0.8
    }
  },
  "metadata": {
    "request_id": "my_task_001"
  }
}
```

## Common Commands

```bash
# Evo2 (requires GPU)
docker-compose -f docker-compose.microservices.yml run --rm evo2 \
  --input /data/input/task.json

# CodonTransformer (CPU ok)
docker-compose -f docker-compose.microservices.yml run --rm codon_transformer \
  --input /data/input/task.json

# CodonVerifier (CPU only)
docker-compose -f docker-compose.microservices.yml run --rm codon_verifier \
  --input /data/input/task.json
```

## Batch Processing 100 Files

```bash
# Put 100 JSON files in data/input/
# Then:
python scripts/batch_process.py \
  --service evo2 \
  --input-dir data/input/ \
  --workers 10

# Results in data/output/evo2/
```

## Full Pipeline

```bash
python scripts/pipeline.py --input data/input/my_sequence.json
```

This runs: Evo2 → CodonTransformer → CodonVerifier automatically.

## Troubleshooting

**"No such file or directory"**
```bash
mkdir -p data/input data/output logs
```

**"Permission denied"**
```bash
chmod -R 755 data/ logs/
```

**"Out of memory"**
```bash
# Reduce workers
python scripts/batch_process.py --workers 2 ...
```

## Next Steps

- Read `README.microservices.md` for detailed usage
- See `ARCHITECTURE.md` for design details
- Check `data/output/` for results

## Why Microservices?

✅ No dependency conflicts (each service isolated)  
✅ Easy batch processing (run 100 tasks in parallel)  
✅ Simple updates (update one service at a time)  
✅ Fault isolation (one crash doesn't break others)

**vs. Old Monolithic Dockerfile**: That had setuptools conflicts and couldn't batch process easily.


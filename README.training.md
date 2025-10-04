# Training Service - Microservices Model Training

## 🎯 Overview

The **Training Service** is a microservice dedicated to training surrogate models using the microservices architecture. It integrates seamlessly with the existing services and provides a standardized way to train models with different configurations.

## ✨ Features

- ✅ **Unified Training** - Train a single model across multiple hosts
- ✅ **Host-Specific Training** - Train separate models for each host organism
- ✅ **Flexible Configuration** - JSON-based configuration for all parameters
- ✅ **Batch Processing** - Train multiple model configurations in parallel
- ✅ **Isolated Environment** - No dependency conflicts with other services

## 🚀 Quick Start

### Step 1: Build the Training Service

```bash
# Build the training service
docker-compose -f docker-compose.microservices.yml build training
```

### Step 2: Run Training with Example Data

#### Quick Test with Toy Dataset

```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_toy.json
```

#### Train Unified Multi-Host Model

```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_unified.json
```

#### Train Host-Specific Models

```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_host_specific.json
```

### Step 3: Check Training Results

```bash
# View trained models
ls -lh models/

# View training logs
cat data/output/training/*_result.json
```

## 📋 Configuration Format

Training tasks are defined using JSON configuration files. Here's the structure:

```json
{
  "task": "train_unified",
  "config": {
    "data_paths": ["/data/converted/merged_dataset.jsonl"],
    "output_path": "/data/output/models/model.pkl",
    "mode": "unified",
    "data_config": {
      "max_samples_per_host": null,
      "min_sequence_length": 10,
      "max_sequence_length": 10000,
      "filter_reviewed_only": false,
      "balance_hosts": true
    },
    "surrogate_config": {
      "quantile_hi": 0.9,
      "test_size": 0.15
    },
    "target_hosts": null,
    "max_samples": 5000
  },
  "metadata": {
    "request_id": "training_001",
    "description": "Training description"
  }
}
```

### Configuration Parameters

#### Top-Level Fields
- **task**: Task type (`train_unified` or `train_host_specific`)
- **config**: Training configuration object
- **metadata**: Optional metadata for tracking

#### config Object
- **data_paths**: List of JSONL data file paths (required)
- **output_path**: Path to save the trained model (required)
- **mode**: Training mode - `"unified"` or `"host-specific"` (required)
- **target_hosts**: List of specific hosts to include (optional)
- **max_samples**: Maximum number of total samples to use (optional)

#### data_config Object
- **max_samples_per_host**: Maximum samples per host organism
- **min_sequence_length**: Minimum sequence length to include (default: 10)
- **max_sequence_length**: Maximum sequence length to include (default: 10000)
- **filter_reviewed_only**: Only include reviewed entries (default: false)
- **balance_hosts**: Balance samples across hosts (default: false)

#### surrogate_config Object
- **quantile_hi**: High quantile threshold for classification (default: 0.9)
- **test_size**: Fraction of data for testing (default: 0.15)

## 📝 Example Use Cases

### 1. Quick Test Training

Test the training pipeline with the toy dataset:

```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_toy.json
```

This trains a small model quickly to verify the setup works.

### 2. Production Unified Model

Train a unified model with balanced multi-host data:

```json
{
  "task": "train_unified",
  "config": {
    "data_paths": ["/data/converted/merged_dataset.jsonl"],
    "output_path": "/data/output/models/production_unified.pkl",
    "mode": "unified",
    "data_config": {
      "balance_hosts": true,
      "filter_reviewed_only": true,
      "max_samples_per_host": 5000
    },
    "max_samples": 20000
  }
}
```

### 3. Host-Specific Models for Key Organisms

Train separate models for E. coli, Human, and Mouse:

```json
{
  "task": "train_host_specific",
  "config": {
    "data_paths": ["/data/converted/merged_dataset.jsonl"],
    "output_path": "/data/output/models/host_specific/model.pkl",
    "mode": "host-specific",
    "target_hosts": ["E_coli", "Human", "Mouse"],
    "data_config": {
      "filter_reviewed_only": true,
      "max_samples_per_host": 2000
    }
  }
}
```

## 🔧 Advanced Usage

### Custom Output Location

Specify a custom output path for the results JSON:

```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/my_training.json \
  --output /data/output/my_results.json
```

### Training Multiple Configurations

Create multiple configuration files and train them in sequence:

```bash
for config in data/input/training_*.json; do
  echo "Training with $config..."
  docker-compose -f docker-compose.microservices.yml run --rm training \
    --input /data/$config
done
```

### Parallel Training (Different Hosts)

You can run multiple training containers in parallel if training host-specific models:

```bash
# Terminal 1
docker-compose -f docker-compose.microservices.yml run --rm \
  --name training-ecoli training \
  --input /data/input/training_ecoli.json

# Terminal 2
docker-compose -f docker-compose.microservices.yml run --rm \
  --name training-human training \
  --input /data/input/training_human.json
```

## 📊 Training Output

The service produces two types of output:

### 1. Trained Model Files
- **Location**: Specified in `output_path`
- **Format**: `.pkl` (pickled scikit-learn model)
- **Contains**: Trained surrogate model with all parameters

### 2. Results JSON
- **Location**: `/data/output/training/` (or specified with `--output`)
- **Format**: JSON with training metrics and metadata

Example output:

```json
{
  "task": "train_unified",
  "status": "success",
  "output": {
    "mode": "unified",
    "model_path": "/data/output/models/unified_multihost.pkl",
    "metrics": {
      "train_accuracy": 0.856,
      "test_accuracy": 0.843,
      "n_samples": 5000,
      "n_features": 42,
      "host_distribution": {
        "E_coli": 1500,
        "Human": 1500,
        "Mouse": 1000,
        "S_cerevisiae": 1000
      }
    }
  },
  "metadata": {
    "request_id": "training_unified_001",
    "processing_time_seconds": 45.67,
    "service": "training",
    "version": "1.0.0"
  }
}
```

## 🐛 Troubleshooting

### Issue: "Data file not found"

**Solution**: Make sure data files exist and paths are correct. Remember paths inside the container use `/data/` prefix:

```bash
# Check if data exists
ls -lh data/converted/merged_dataset.jsonl

# Use absolute path in config
"data_paths": ["/data/converted/merged_dataset.jsonl"]
```

### Issue: "No records loaded"

**Solution**: Check data format and filters. Try reducing filtering:

```json
"data_config": {
  "filter_reviewed_only": false,
  "min_sequence_length": 1,
  "max_sequence_length": 100000
}
```

### Issue: Container fails to build

**Solution**: Rebuild with no cache:

```bash
docker-compose -f docker-compose.microservices.yml build --no-cache training
```

## 🔗 Integration with Other Services

After training a model, you can use it with the CodonVerifier service:

```bash
# 1. Train model
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_unified.json

# 2. Use trained model for verification
docker-compose -f docker-compose.microservices.yml run --rm codon_verifier \
  --input /data/input/verify_task.json \
  --model /data/output/models/unified_multihost.pkl
```

## 📚 Related Documentation

- [Microservices Architecture](ARCHITECTURE.md)
- [Quick Start Guide](QUICKSTART.md)
- [Multi-Host Dataset Guide](docs/MULTIHOST_DATASET_GUIDE.md)
- [Training Script Documentation](codon_verifier/train_surrogate_multihost.py)

## 💡 Tips

1. **Start Small**: Test with toy dataset before training on full data
2. **Balance Hosts**: Use `balance_hosts: true` for better multi-host performance
3. **Monitor Resources**: Training can be memory-intensive with large datasets
4. **Save Configurations**: Keep training configs in version control for reproducibility
5. **Check Logs**: Review training logs in `/logs/` for detailed information

## 🤝 Support

For issues or questions:
1. Check [TROUBLESHOOTING](docs/TROUBLESHOOTING.md)
2. Review training logs in `logs/` directory
3. Verify data format matches expected structure


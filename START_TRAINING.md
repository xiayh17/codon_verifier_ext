# 🚀 Quick Start: Model Training with Microservices

## ✅ What's Been Set Up

I've created a **Training Service** for your microservices architecture that allows you to train surrogate models using containerized, isolated environments.

### New Components Added:

1. **Training Service** (`services/training/`)
   - Dockerfile for training environment
   - Service application (`app.py`)
   - Utility functions (`utils.py`)

2. **Docker Compose Integration**
   - Added `training` service to `docker-compose.microservices.yml`
   - Configured volume mounts for data and models

3. **Training Configuration Files** (`data/input/`)
   - `training_toy.json` - Quick test with toy dataset
   - `training_unified.json` - Unified multi-host training
   - `training_host_specific.json` - Host-specific model training

4. **Helper Scripts**
   - `scripts/train_with_microservices.sh` - Convenient training script
   - Documentation in `README.training.md`

---

## 🎯 Quick Start - 3 Commands

### 1. Build the Training Service

```bash
cd /mnt/c/Users/xiayh17/Projects/coursepicker_starter/coursepicker/codon_verifier_ext
docker-compose -f docker-compose.microservices.yml build training
```

### 2. Run Quick Test Training

```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_toy.json
```

### 3. Check Results

```bash
# View training results
cat data/output/training/training_toy_result.json

# View trained models (after unified training)
ls -lh models/
```

---

## 📋 Training Modes

### Mode 1: Quick Test (Toy Dataset)

Perfect for testing the pipeline works:

```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_toy.json
```

**Output**: `/data/output/models/toy_model.pkl`
**Time**: ~1 second
**Data**: 3 toy samples

### Mode 2: Unified Multi-Host Model

Train a single model across all host organisms:

```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_unified.json
```

**Output**: `/data/output/models/unified_multihost.pkl`
**Features**:
- Balanced sampling across hosts
- Supports E. coli, Human, Mouse, S. cerevisiae, P. pastoris, etc.
- Configurable sample limits

### Mode 3: Host-Specific Models

Train separate models for each host organism:

```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_host_specific.json
```

**Output**: `/data/output/models/host_specific/{host}_surrogate.pkl`
**Hosts**: E_coli, Human, Mouse (configurable)

---

## 🔧 Using the Convenience Script

The `scripts/train_with_microservices.sh` script makes training even easier:

```bash
# Make it executable (first time only)
chmod +x scripts/train_with_microservices.sh

# Quick test
./scripts/train_with_microservices.sh --build --mode toy

# Train unified model
./scripts/train_with_microservices.sh --mode unified

# Train host-specific models
./scripts/train_with_microservices.sh --mode host-specific

# Use custom configuration
./scripts/train_with_microservices.sh --config data/input/my_config.json
```

---

## 📝 Configuration Format

Training tasks are defined in JSON files. Here's the structure:

```json
{
  "task": "train_unified",
  "config": {
    "data_paths": ["/data/converted/merged_dataset.jsonl"],
    "output_path": "/data/output/models/model.pkl",
    "mode": "unified",
    "data_config": {
      "balance_hosts": true,
      "filter_reviewed_only": false,
      "max_samples_per_host": 1000
    },
    "surrogate_config": {
      "quantile_hi": 0.9,
      "test_size": 0.15
    },
    "target_hosts": ["E_coli", "Human"],
    "max_samples": 5000
  },
  "metadata": {
    "request_id": "training_001",
    "description": "Training description"
  }
}
```

### Key Parameters:

- **data_paths**: List of JSONL files to use for training
- **output_path**: Where to save the trained model
- **mode**: `"unified"` or `"host-specific"`
- **balance_hosts**: Balance samples across different hosts
- **max_samples**: Limit total training samples
- **target_hosts**: Filter to specific hosts

---

## 🌟 Example Workflows

### Workflow 1: Train on Your Multi-Host Dataset

If you have `data/converted/merged_dataset.jsonl`:

```bash
# Edit training_unified.json to adjust parameters if needed
nano data/input/training_unified.json

# Train the model
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_unified.json

# Check results
cat data/output/training/training_unified_result.json
```

### Workflow 2: Train Multiple Models in Batch

```bash
# Create multiple config files
for host in E_coli Human Mouse; do
  cat > data/input/training_${host}.json <<EOF
{
  "task": "train_unified",
  "config": {
    "data_paths": ["/data/converted/merged_dataset.jsonl"],
    "output_path": "/data/output/models/${host}_model.pkl",
    "mode": "unified",
    "target_hosts": ["${host}"],
    "data_config": {"balance_hosts": false}
  }
}
EOF
done

# Train all models
for config in data/input/training_E_coli.json data/input/training_Human.json data/input/training_Mouse.json; do
  echo "Training with $config..."
  docker-compose -f docker-compose.microservices.yml run --rm training \
    --input /data/$(basename $config)
done
```

---

## 📊 Understanding Training Output

The training service produces two types of output:

### 1. Training Results JSON

Location: `data/output/training/[config_name]_result.json`

Example:
```json
{
  "task": "train_unified",
  "status": "success",
  "output": {
    "mode": "unified",
    "model_path": "/data/output/models/unified_multihost.pkl",
    "metrics": {
      "r2_mu": 0.843,
      "mae_mu": 0.234,
      "sigma_mean": 0.156,
      "n_test": 750,
      "n_samples": 5000,
      "n_features": 90,
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

### 2. Trained Model Files

Location: `models/` or specified `output_path`
Format: `.pkl` (pickled scikit-learn pipeline)

---

## 🔗 Integration with Other Services

After training, use your models with other services:

```bash
# 1. Train a model
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_unified.json

# 2. Use with CodonVerifier service
docker-compose -f docker-compose.microservices.yml run --rm codon_verifier \
  --input /data/input/verify_sequences.json \
  --model /data/output/models/unified_multihost.pkl
```

---

## 💡 Tips and Best Practices

1. **Start Small**: Always test with `training_toy.json` first to verify setup
2. **Monitor Resources**: Training can be memory-intensive with large datasets
3. **Balance Data**: Use `balance_hosts: true` for better multi-host performance
4. **Check Logs**: Review logs in `data/output/training/` for detailed information
5. **Save Configurations**: Keep training configs in version control for reproducibility

---

## 🐛 Troubleshooting

### Issue: "Data file not found"

**Solution**: Ensure data paths in config use `/data/` prefix for mounted volumes:
```json
"data_paths": ["/data/converted/merged_dataset.jsonl"]
```

### Issue: "No records loaded"

**Solution**: Check data format and filters:
```bash
# Verify data file exists
ls -lh data/converted/merged_dataset.jsonl

# Relax filters in config
"data_config": {
  "filter_reviewed_only": false,
  "min_sequence_length": 1
}
```

### Issue: Container build fails

**Solution**: Rebuild with no cache:
```bash
docker-compose -f docker-compose.microservices.yml build --no-cache training
```

---

## 📚 Additional Documentation

- **[README.training.md](README.training.md)** - Detailed training service documentation
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Microservices architecture overview
- **[QUICKSTART.md](QUICKSTART.md)** - General microservices quick start
- **[docs/MULTIHOST_DATASET_GUIDE.md](docs/MULTIHOST_DATASET_GUIDE.md)** - Multi-host dataset guide

---

## 🎉 Next Steps

Now that you have the training service set up, you can:

1. ✅ Train models using your own data
2. ✅ Experiment with different configurations
3. ✅ Use trained models with other microservices
4. ✅ Scale training by running multiple containers

**Ready to train your first real model?**

```bash
# If you have multi-host data
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_unified.json

# Monitor progress
docker-compose -f docker-compose.microservices.yml logs -f training
```

---

## 🤝 Need Help?

If you encounter issues:
1. Check [README.training.md](README.training.md) for detailed documentation
2. Review training logs in `data/output/training/`
3. Verify data format matches expected JSONL structure
4. Try the toy dataset first to isolate configuration issues

Happy Training! 🚀


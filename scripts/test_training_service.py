#!/usr/bin/env python3
"""
Quick test script for training microservice

Usage:
    # Test with Docker (requires docker-compose)
    python3 scripts/test_training_service.py \
        --input data/test/Ec_enhanced.jsonl \
        --output models/test_surrogate.pkl \
        --use-docker

    # Test without Docker (requires sklearn, lightgbm locally)
    python3 scripts/test_training_service.py \
        --input data/test/Ec_enhanced.jsonl \
        --output models/test_surrogate.pkl
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
import time


def test_training_docker(enhanced_data: Path, model_output: Path):
    """Test training service via Docker Compose"""
    print("=" * 60)
    print("Testing Training Service via Docker Compose")
    print("=" * 60)
    
    # Create training configuration
    config_path = model_output.parent / "training_config_test.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    training_config = {
        "task": "train_unified",
        "config": {
            "data_paths": [f"/data/enhanced/{enhanced_data.name}"],
            "output_path": f"/data/output/models/{model_output.name}",
            "mode": "unified",
            "data_config": {
                "min_sequence_length": 10,
                "max_sequence_length": 10000,
                "filter_reviewed_only": False,
                "balance_hosts": False
            },
            "surrogate_config": {
                "quantile_hi": 0.9,
                "test_size": 0.15
            }
        },
        "metadata": {
            "request_id": f"test_train_{int(time.time())}"
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(training_config, f, indent=2)
    
    print(f"✓ Configuration saved to: {config_path}")
    print(f"  Input data: {enhanced_data}")
    print(f"  Output model: {model_output}")
    print()
    
    # Build docker-compose command
    cmd = [
        "docker-compose",
        "-f", "docker-compose.microservices.yml",
        "run", "--rm",
        "-v", f"{enhanced_data.parent.absolute()}:/data/enhanced:ro",
        "-v", f"{model_output.parent.absolute()}:/data/output/models",
        "-v", f"{config_path.parent.absolute()}:/data/config",
        "training",
        "--input", f"/data/config/{config_path.name}"
    ]
    
    print("Command:")
    print(f"  {' '.join(cmd)}")
    print()
    print("Starting training (this may take a few minutes)...")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, check=True)
        print("-" * 60)
        print(f"✓ Training completed successfully!")
        print(f"✓ Model saved to: {model_output}")
        
        # Clean up config
        config_path.unlink()
        
        return True
    
    except subprocess.CalledProcessError as e:
        print("-" * 60)
        print(f"✗ Training failed: {e}")
        return False


def test_training_local(enhanced_data: Path, model_output: Path):
    """Test training locally (requires sklearn, lightgbm)"""
    print("=" * 60)
    print("Testing Training Locally (requires sklearn, lightgbm)")
    print("=" * 60)
    
    cmd = [
        "python3", "-m", "codon_verifier.train_surrogate_multihost",
        "--data", str(enhanced_data),
        "--out", str(model_output),
        "--mode", "unified"
    ]
    
    print("Command:")
    print(f"  {' '.join(cmd)}")
    print()
    print("Starting training (this may take a few minutes)...")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("-" * 60)
        print(f"✓ Training completed successfully!")
        print(f"✓ Model saved to: {model_output}")
        return True
    
    except subprocess.CalledProcessError as e:
        print(result.stderr if 'result' in locals() else str(e))
        print("-" * 60)
        print(f"✗ Training failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Test Training Microservice',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input enhanced JSONL file'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output model path (.pkl)'
    )
    parser.add_argument(
        '--use-docker',
        action='store_true',
        help='Use Docker Compose training service'
    )
    
    args = parser.parse_args()
    
    # Validate input
    enhanced_data = Path(args.input)
    if not enhanced_data.exists():
        print(f"✗ Input file not found: {enhanced_data}")
        sys.exit(1)
    
    model_output = Path(args.output)
    model_output.parent.mkdir(parents=True, exist_ok=True)
    
    # Run test
    if args.use_docker:
        success = test_training_docker(enhanced_data, model_output)
    else:
        success = test_training_local(enhanced_data, model_output)
    
    if success:
        print()
        print("=" * 60)
        print("✓ Test passed!")
        print("=" * 60)
        
        # Verify model file exists
        if model_output.exists():
            size = model_output.stat().st_size / 1024  # KB
            print(f"Model file size: {size:.2f} KB")
            print()
            print("You can now use this model:")
            print(f"  python3 -m codon_verifier.surrogate_infer_demo \\")
            print(f"    --model {model_output} \\")
            print(f"    --seq ATGGCT... ATGGCA...")
        sys.exit(0)
    else:
        print()
        print("=" * 60)
        print("✗ Test failed!")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()


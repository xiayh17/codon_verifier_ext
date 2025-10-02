#!/usr/bin/env python
"""
Example Python script demonstrating multi-host dataset usage.

This script shows how to:
1. Convert UniProt TSV data to JSONL
2. Load and mix multi-host data
3. Train surrogate models
4. Use models for prediction
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from codon_verifier.data_converter import convert_dataset_directory, ORGANISM_MAP
from codon_verifier.data_loader import (
    DataLoader,
    DataConfig,
    create_train_val_split,
    merge_datasets
)
from codon_verifier.train_surrogate_multihost import (
    train_unified_model,
    train_host_specific_models
)
from codon_verifier.surrogate import load_and_predict
from codon_verifier.hosts.tables import get_host_tables


def example_data_conversion():
    """Example: Convert TSV to JSONL"""
    print("\n" + "="*60)
    print("Example 1: Data Conversion")
    print("="*60)
    
    # Assume we have TSV files in ./data/dataset/
    input_dir = "./data/2025_bio-os_data/dataset"
    output_dir = "./outputs/converted"
    
    if not os.path.exists(input_dir):
        print(f"⚠ Input directory not found: {input_dir}")
        print("  Please download and extract the dataset first")
        return
    
    print(f"Converting TSV files from {input_dir}...")
    
    stats = convert_dataset_directory(
        dataset_dir=input_dir,
        output_dir=output_dir,
        max_per_file=1000,  # Limit for demo
        filter_reviewed=True,  # Only reviewed entries
        merge_output=True  # Merge into single file
    )
    
    print("\nConversion statistics:")
    for filename, file_stats in stats.items():
        print(f"  {filename}: {file_stats['valid_records']} valid records")
    
    print(f"\n✓ Output saved to: {output_dir}/merged_dataset.jsonl")


def example_data_loading():
    """Example: Load and mix multi-host data"""
    print("\n" + "="*60)
    print("Example 2: Data Loading and Mixing")
    print("="*60)
    
    # Configure data loader
    config = DataConfig(
        min_sequence_length=50,
        max_sequence_length=2000,
        filter_reviewed_only=True,
        balance_hosts=True,
        max_samples_per_host=500,
    )
    
    loader = DataLoader(config)
    
    # Load data from multiple files
    data_files = [
        "./outputs/converted/Ec.jsonl",
        "./outputs/converted/Human.jsonl",
        "./outputs/converted/mouse.jsonl",
    ]
    
    # Check which files exist
    existing_files = [f for f in data_files if os.path.exists(f)]
    
    if not existing_files:
        print("⚠ No data files found. Please run data conversion first.")
        return
    
    print(f"Loading data from {len(existing_files)} files...")
    
    records = loader.load_and_mix(
        existing_files,
        target_hosts={'E_coli', 'Human', 'Mouse'},
        total_samples=1500
    )
    
    print(f"\n✓ Loaded {len(records)} total records")
    
    # Show distribution
    from collections import Counter
    host_dist = Counter(r.get('host', 'unknown') for r in records)
    print("\nHost distribution:")
    for host, count in host_dist.items():
        print(f"  {host}: {count}")
    
    return records


def example_unified_training():
    """Example: Train unified multi-host model"""
    print("\n" + "="*60)
    print("Example 3: Unified Model Training")
    print("="*60)
    
    data_files = ["./outputs/converted/merged_dataset.jsonl"]
    
    if not os.path.exists(data_files[0]):
        print(f"⚠ Data file not found: {data_files[0]}")
        return None
    
    output_model = "./outputs/models/unified_demo.pkl"
    os.makedirs(os.path.dirname(output_model), exist_ok=True)
    
    print("Training unified model across all hosts...")
    
    data_config = DataConfig(
        balance_hosts=True,
        max_samples_per_host=300,
    )
    
    try:
        metrics = train_unified_model(
            data_paths=data_files,
            output_model_path=output_model,
            data_config=data_config,
            max_samples=1000
        )
        
        print("\nTraining metrics:")
        print(f"  R² score: {metrics['r2_mu']:.3f}")
        print(f"  MAE: {metrics['mae_mu']:.3f}")
        print(f"  Samples: {metrics['n_samples']}")
        print(f"  Features: {metrics['n_features']}")
        
        print(f"\n✓ Model saved to: {output_model}")
        return output_model
        
    except Exception as e:
        print(f"✗ Training failed: {e}")
        return None


def example_prediction(model_path: str):
    """Example: Use trained model for prediction"""
    print("\n" + "="*60)
    print("Example 4: Model Prediction")
    print("="*60)
    
    if not os.path.exists(model_path):
        print(f"⚠ Model not found: {model_path}")
        return
    
    # Example sequences to predict
    test_sequences = [
        "ATGGCTGCTGCTGCTGCTGCT",  # Simple Ala repeat
        "ATGGCCGCCGCCGCCGCCGCC",  # Different codon for Ala
        "ATGAAAGAAGAAGAAGAAGAA",  # Lys repeat
    ]
    
    # Predict for E. coli
    print("Predicting expression levels for E. coli...")
    usage, trna_w = get_host_tables("E_coli")
    
    predictions = load_and_predict(
        model_path,
        test_sequences,
        usage=usage,
        trna_w=trna_w
    )
    
    print("\nPredictions:")
    for i, (seq, pred) in enumerate(zip(test_sequences, predictions)):
        print(f"  Seq {i+1}: μ={pred['mu']:.2f}, σ={pred['sigma']:.2f}")
    
    print("\n✓ Prediction complete")


def example_host_specific_training():
    """Example: Train host-specific models"""
    print("\n" + "="*60)
    print("Example 5: Host-Specific Model Training")
    print("="*60)
    
    data_files = ["./outputs/converted/merged_dataset.jsonl"]
    
    if not os.path.exists(data_files[0]):
        print(f"⚠ Data file not found: {data_files[0]}")
        return
    
    output_dir = "./outputs/models/host_specific"
    os.makedirs(output_dir, exist_ok=True)
    
    print("Training separate models for each host...")
    
    data_config = DataConfig(
        filter_reviewed_only=True,
        min_sequence_length=50,
    )
    
    try:
        all_metrics = train_host_specific_models(
            data_paths=data_files,
            output_dir=output_dir,
            data_config=data_config,
            target_hosts=['E_coli', 'Human', 'Mouse']
        )
        
        print("\nHost-specific models trained:")
        for host, metrics in all_metrics.items():
            print(f"\n  {host}:")
            print(f"    R² score: {metrics['r2_mu']:.3f}")
            print(f"    MAE: {metrics['mae_mu']:.3f}")
            print(f"    Samples: {metrics['n_samples']}")
            print(f"    Path: {metrics['model_path']}")
        
        print(f"\n✓ Models saved to: {output_dir}")
        
    except Exception as e:
        print(f"✗ Training failed: {e}")


def main():
    """Run all examples"""
    print("="*60)
    print("Multi-Host Dataset Examples")
    print("="*60)
    print("\nAvailable organisms:")
    for org, host in ORGANISM_MAP.items():
        print(f"  {org} -> {host}")
    
    # Example 1: Data conversion
    # Uncomment to run:
    # example_data_conversion()
    
    # Example 2: Data loading
    records = example_data_loading()
    
    # Example 3: Unified training
    # Uncomment to run:
    # model_path = example_unified_training()
    # if model_path:
    #     example_prediction(model_path)
    
    # Example 5: Host-specific training
    # Uncomment to run:
    # example_host_specific_training()
    
    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60)
    print("\nTo run full pipeline, uncomment the examples in main()")


if __name__ == "__main__":
    main()


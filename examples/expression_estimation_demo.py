#!/usr/bin/env python3
"""
Expression Estimation Demo

This script demonstrates how to use the enhanced expression estimator
with Evo2 model features.

Author: Codon Verifier Team
Date: 2025-10-04
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from codon_verifier.expression_estimator import (
    ExpressionEstimator,
    estimate_expression_enhanced,
    estimate_expression_from_metadata
)


def demo_basic_usage():
    """Demo 1: Basic metadata-only estimation (baseline)"""
    print("=" * 60)
    print("Demo 1: Basic Metadata-Only Estimation")
    print("=" * 60)
    
    expr, conf = estimate_expression_from_metadata(
        reviewed="reviewed",
        subcellular_location="cytoplasm",
        protein_length=250,
        organism="E. coli"
    )
    
    print(f"Protein: E. coli cytoplasmic protein (250 aa)")
    print(f"Expression estimate: {expr:.1f}")
    print(f"Confidence: {conf}")
    print()


def demo_model_enhanced():
    """Demo 2: Model-enhanced estimation with Evo2 features"""
    print("=" * 60)
    print("Demo 2: Model-Enhanced Estimation")
    print("=" * 60)
    
    # Case 1: High-quality sequence (high Evo2 confidence)
    print("\nCase 1: High-quality sequence")
    model_features_good = {
        "avg_confidence": 0.93,
        "max_confidence": 0.96,
        "min_confidence": 0.90,
        "avg_loglik": -1.2,
        "perplexity": 6.5
    }
    
    expr_baseline, conf_baseline = estimate_expression_enhanced(
        reviewed="reviewed",
        subcellular_location="cytoplasm",
        protein_length=250,
        organism="E. coli",
        mode="metadata_only"
    )
    
    expr_enhanced, conf_enhanced = estimate_expression_enhanced(
        reviewed="reviewed",
        subcellular_location="cytoplasm",
        protein_length=250,
        organism="E. coli",
        model_features=model_features_good,
        mode="model_enhanced"
    )
    
    print(f"  Metadata only:  {expr_baseline:.2f} ({conf_baseline})")
    print(f"  Model enhanced: {expr_enhanced:.2f} ({conf_enhanced})")
    print(f"  Change: +{expr_enhanced - expr_baseline:.2f}")
    print(f"  Evo2 features:")
    print(f"    - Avg confidence: {model_features_good['avg_confidence']:.3f}")
    print(f"    - Avg log-likelihood: {model_features_good['avg_loglik']:.2f}")
    print(f"    - Perplexity: {model_features_good['perplexity']:.1f}")
    
    # Case 2: Low-quality sequence (low Evo2 confidence)
    print("\nCase 2: Low-quality sequence")
    model_features_bad = {
        "avg_confidence": 0.65,
        "max_confidence": 0.75,
        "min_confidence": 0.55,
        "avg_loglik": -4.8,
        "perplexity": 45.2
    }
    
    expr_enhanced_bad, conf_enhanced_bad = estimate_expression_enhanced(
        reviewed="reviewed",
        subcellular_location="cytoplasm",
        protein_length=250,
        organism="E. coli",
        model_features=model_features_bad,
        mode="model_enhanced"
    )
    
    print(f"  Metadata only:  {expr_baseline:.2f} ({conf_baseline})")
    print(f"  Model enhanced: {expr_enhanced_bad:.2f} ({conf_enhanced_bad})")
    print(f"  Change: {expr_enhanced_bad - expr_baseline:.2f}")
    print(f"  Evo2 features:")
    print(f"    - Avg confidence: {model_features_bad['avg_confidence']:.3f}")
    print(f"    - Avg log-likelihood: {model_features_bad['avg_loglik']:.2f}")
    print(f"    - Perplexity: {model_features_bad['perplexity']:.1f}")
    print()


def demo_full_mode():
    """Demo 3: Full mode with sequence features"""
    print("=" * 60)
    print("Demo 3: Full Mode (Metadata + Model + Sequence)")
    print("=" * 60)
    
    # GFP-like sequence fragment (optimal GC content)
    sequence_good = "ATGGCTGCAGGCGGTGGCGGCGGTGGCGCAGGCGGCGGTGGCGCA"
    
    # Poor sequence with extreme GC and homopolymers
    sequence_bad = "ATGGGGGGGGGGGGAAAAAAAAAAACCCCCCCCCCTTTTTTTTTT"
    
    model_features = {
        "avg_confidence": 0.90,
        "avg_loglik": -2.0,
        "perplexity": 10.0
    }
    
    estimator = ExpressionEstimator(mode="full")
    
    print("\nGood sequence (balanced GC, no long homopolymers):")
    expr_good, conf_good = estimator.estimate(
        reviewed="reviewed",
        subcellular_location="cytoplasm",
        protein_length=250,
        organism="E. coli",
        model_features=model_features,
        sequence=sequence_good
    )
    print(f"  Sequence: {sequence_good[:30]}...")
    gc_good = (sequence_good.count('G') + sequence_good.count('C')) / len(sequence_good)
    print(f"  GC content: {gc_good:.2f}")
    print(f"  Expression: {expr_good:.2f} ({conf_good})")
    
    print("\nBad sequence (extreme homopolymers):")
    expr_bad, conf_bad = estimator.estimate(
        reviewed="reviewed",
        subcellular_location="cytoplasm",
        protein_length=250,
        organism="E. coli",
        model_features=model_features,
        sequence=sequence_bad
    )
    print(f"  Sequence: {sequence_bad[:30]}...")
    gc_bad = (sequence_bad.count('G') + sequence_bad.count('C')) / len(sequence_bad)
    print(f"  GC content: {gc_bad:.2f}")
    print(f"  Expression: {expr_bad:.2f} ({conf_bad})")
    print(f"  Penalty: -{expr_good - expr_bad:.2f} (due to homopolymers)")
    print()


def demo_comparison_table():
    """Demo 4: Comprehensive comparison across proteins"""
    print("=" * 60)
    print("Demo 4: Comparison Across Different Proteins")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Ribosomal protein (high expression)",
            "reviewed": "reviewed",
            "location": "ribosome",
            "length": 120,
            "model": {"avg_confidence": 0.94, "avg_loglik": -1.1, "perplexity": 5.8}
        },
        {
            "name": "Membrane protein (low expression)",
            "reviewed": "reviewed",
            "location": "membrane",
            "length": 450,
            "model": {"avg_confidence": 0.85, "avg_loglik": -2.5, "perplexity": 15.2}
        },
        {
            "name": "Secreted protein",
            "reviewed": "reviewed",
            "location": "secreted",
            "length": 300,
            "model": {"avg_confidence": 0.88, "avg_loglik": -1.8, "perplexity": 9.5}
        },
        {
            "name": "Uncharacterized protein",
            "reviewed": "unreviewed",
            "location": "",
            "length": 180,
            "model": {"avg_confidence": 0.75, "avg_loglik": -3.2, "perplexity": 25.0}
        }
    ]
    
    print("\n{:<35} {:>12} {:>12} {:>10}".format(
        "Protein", "Metadata", "Enhanced", "Δ"
    ))
    print("-" * 70)
    
    for case in test_cases:
        expr_meta, _ = estimate_expression_enhanced(
            reviewed=case["reviewed"],
            subcellular_location=case["location"],
            protein_length=case["length"],
            organism="E. coli",
            mode="metadata_only"
        )
        
        expr_enh, conf = estimate_expression_enhanced(
            reviewed=case["reviewed"],
            subcellular_location=case["location"],
            protein_length=case["length"],
            organism="E. coli",
            model_features=case["model"],
            mode="model_enhanced"
        )
        
        delta = expr_enh - expr_meta
        delta_str = f"+{delta:.1f}" if delta > 0 else f"{delta:.1f}"
        
        print("{:<35} {:>12.1f} {:>12.1f} {:>10}".format(
            case["name"], expr_meta, expr_enh, delta_str
        ))
    
    print()


def demo_evo2_feature_impact():
    """Demo 5: Show impact of individual Evo2 features"""
    print("=" * 60)
    print("Demo 5: Impact of Individual Evo2 Features")
    print("=" * 60)
    
    base_params = {
        "reviewed": "reviewed",
        "subcellular_location": "cytoplasm",
        "protein_length": 250,
        "organism": "E. coli"
    }
    
    # Baseline (no model features)
    expr_baseline, _ = estimate_expression_enhanced(
        **base_params,
        mode="metadata_only"
    )
    print(f"\nBaseline (metadata only): {expr_baseline:.2f}")
    
    # Vary confidence
    print("\n--- Varying Confidence Score ---")
    for conf_score in [0.60, 0.75, 0.85, 0.92, 0.96]:
        expr, _ = estimate_expression_enhanced(
            **base_params,
            model_features={"avg_confidence": conf_score},
            mode="model_enhanced"
        )
        delta = expr - expr_baseline
        print(f"  Confidence {conf_score:.2f} → Expression {expr:.2f} (Δ {delta:+.2f})")
    
    # Vary log-likelihood
    print("\n--- Varying Log-Likelihood ---")
    for loglik in [-5.0, -3.0, -2.0, -1.0, -0.5]:
        expr, _ = estimate_expression_enhanced(
            **base_params,
            model_features={"avg_loglik": loglik},
            mode="model_enhanced"
        )
        delta = expr - expr_baseline
        print(f"  Log-lik {loglik:.1f} → Expression {expr:.2f} (Δ {delta:+.2f})")
    
    # Vary perplexity
    print("\n--- Varying Perplexity ---")
    for perp in [50.0, 30.0, 15.0, 8.0, 3.0]:
        expr, _ = estimate_expression_enhanced(
            **base_params,
            model_features={"perplexity": perp},
            mode="model_enhanced"
        )
        delta = expr - expr_baseline
        print(f"  Perplexity {perp:.1f} → Expression {expr:.2f} (Δ {delta:+.2f})")
    
    print()


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print(" Enhanced Expression Estimation - Interactive Demo")
    print("=" * 60 + "\n")
    
    demo_basic_usage()
    demo_model_enhanced()
    demo_full_mode()
    demo_comparison_table()
    demo_evo2_feature_impact()
    
    print("=" * 60)
    print("Demo completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run enhance_expression_estimates.py on your dataset")
    print("2. Train a surrogate model with the enhanced data")
    print("3. Compare performance with the original baseline")
    print("\nSee docs/EXPRESSION_ESTIMATION.md for detailed documentation")
    print()


if __name__ == '__main__':
    main()


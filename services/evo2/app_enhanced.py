#!/usr/bin/env python3
"""
Enhanced Evo2 Service - DNA Sequence Analysis with Real Model Features

This service provides real Evo2 model features (confidence, likelihood, perplexity)
for expression estimation enhancement.

Usage:
    docker-compose -f docker-compose.microservices.yml run --rm evo2 \\
        --input /data/converted/merged_dataset.jsonl \\
        --mode features
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import time
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('evo2-service-enhanced')


def load_evo2_model():
    """
    Load Evo2 model with actual implementation.
    
    Tries multiple backends:
    1. Local evo2 package
    2. NVIDIA NIM API
    3. Fallback to heuristic scoring
    """
    try:
        # Try importing evo2_adapter for real model
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from codon_verifier.evo2_adapter import check_evo2_available, score_sequence
        
        if check_evo2_available():
            logger.info("✓ Real Evo2 model available (local or NIM)")
            return {"backend": "evo2", "score_fn": score_sequence}
        else:
            logger.warning("Evo2 not available, using heuristic backend")
            return {"backend": "heuristic", "score_fn": heuristic_score}
    
    except ImportError:
        logger.warning("evo2_adapter not found, using heuristic backend")
        return {"backend": "heuristic", "score_fn": heuristic_score}


def heuristic_score(dna: str, **kwargs) -> Dict[str, float]:
    """
    Heuristic scoring when real Evo2 is not available.
    
    This provides reasonable estimates based on sequence properties.
    """
    # GC content
    gc_count = dna.count('G') + dna.count('C')
    gc_content = gc_count / len(dna) if len(dna) > 0 else 0.5
    
    # Codon balance (check if codons are used uniformly)
    codons = [dna[i:i+3] for i in range(0, len(dna), 3)]
    from collections import Counter
    codon_freq = Counter(codons)
    codon_entropy = -sum(
        (count / len(codons)) * np.log2(count / len(codons))
        for count in codon_freq.values()
    )
    max_entropy = np.log2(len(codons))
    codon_uniformity = codon_entropy / max_entropy if max_entropy > 0 else 0.5
    
    # Homopolymer runs (penalty for long runs)
    max_run = 1
    current_run = 1
    for i in range(1, len(dna)):
        if dna[i] == dna[i-1]:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 1
    homopolymer_penalty = max(0, (max_run - 8) / 10) if max_run > 8 else 0
    
    # Calculate confidence based on sequence quality
    # Optimal GC: 0.4-0.6, penalize extremes
    gc_score = 1.0 - abs(gc_content - 0.5) * 2  # 1.0 at 0.5, 0.0 at 0 or 1
    gc_score = max(0, gc_score)
    
    # Combine factors
    confidence = 0.5 * gc_score + 0.3 * codon_uniformity - 0.2 * homopolymer_penalty
    confidence = max(0.1, min(0.99, confidence))
    
    # Generate per-position scores (simulate)
    # Add some variation but keep consistent with overall quality
    num_positions = len(dna)
    position_scores = np.random.normal(confidence, 0.05, num_positions)
    position_scores = np.clip(position_scores, 0.1, 0.99)
    
    # Log-likelihood estimate
    # Higher confidence → higher likelihood
    avg_loglik = -5.0 + 4.0 * confidence  # Range: -5 to -1
    
    # Perplexity estimate
    # Lower confidence → higher perplexity
    perplexity = 50.0 * (1.0 - confidence) + 2.0  # Range: 2 to 52
    
    return {
        "avg_confidence": float(confidence),
        "max_confidence": float(np.max(position_scores)),
        "min_confidence": float(np.min(position_scores)),
        "std_confidence": float(np.std(position_scores)),
        "confidence_scores": position_scores.tolist(),
        "avg_loglik": float(avg_loglik),
        "perplexity": float(perplexity),
        "gc_content": float(gc_content),
        "codon_entropy": float(codon_entropy)
    }


def process_sequence_features(
    sequence: str,
    model: Dict,
    request_id: str = "unknown"
) -> Dict[str, Any]:
    """
    Process a single DNA sequence and extract features.
    
    Args:
        sequence: DNA sequence string
        model: Model backend dict
        request_id: Request identifier
        
    Returns:
        Result dict with features
    """
    start_time = time.time()
    
    try:
        # Call scoring function
        score_fn = model["score_fn"]
        features = score_fn(sequence)
        
        # Build result
        result = {
            "task": "extract_features",
            "status": "success",
            "output": {
                "sequence": sequence[:50] + "..." if len(sequence) > 50 else sequence,
                "sequence_length": len(sequence),
                **features,  # Include all extracted features
                "model_version": "evo2-enhanced" if model["backend"] == "evo2" else "heuristic-v1.0",
                "backend": model["backend"]
            },
            "metadata": {
                "request_id": request_id,
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "service": "evo2-enhanced",
                "version": "1.0.0"
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing sequence {request_id}: {e}")
        return {
            "task": "extract_features",
            "status": "error",
            "error": str(e),
            "metadata": {
                "request_id": request_id,
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "service": "evo2-enhanced",
                "version": "1.0.0"
            }
        }


def process_jsonl_records(
    input_path: Path,
    output_path: Path,
    model: Dict,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process JSONL dataset and extract Evo2 features for each sequence.
    
    Args:
        input_path: Input JSONL file path
        output_path: Output JSON file path
        model: Model backend
        limit: Optional limit on number of records to process
        
    Returns:
        Statistics dict
    """
    logger.info("=" * 60)
    logger.info("Evo2 Feature Extraction Pipeline")
    logger.info("=" * 60)
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Backend: {model['backend']}")
    
    results = []
    stats = {
        "total_records": 0,
        "successful": 0,
        "failed": 0,
        "total_time_s": 0.0,
        "avg_time_ms": 0.0
    }
    
    start_time = time.time()
    
    with open(input_path, 'r') as f:
        for idx, line in enumerate(f):
            if limit and idx >= limit:
                logger.info(f"Reached limit of {limit} records")
                break
            
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                sequence = record.get("sequence", "")
                
                if not sequence:
                    logger.warning(f"Record {idx}: No sequence found")
                    continue
                
                # Process sequence
                result = process_sequence_features(
                    sequence=sequence,
                    model=model,
                    request_id=f"record_{idx}"
                )
                
                results.append(result)
                stats["total_records"] += 1
                
                if result["status"] == "success":
                    stats["successful"] += 1
                else:
                    stats["failed"] += 1
                
                # Progress logging
                if (idx + 1) % 1000 == 0:
                    elapsed = time.time() - start_time
                    rate = (idx + 1) / elapsed
                    logger.info(
                        f"Processed {idx + 1} records "
                        f"({rate:.1f} rec/s, {stats['successful']} success, {stats['failed']} failed)"
                    )
            
            except Exception as e:
                logger.error(f"Error processing record {idx}: {e}")
                stats["failed"] += 1
                continue
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Final statistics
    stats["total_time_s"] = time.time() - start_time
    stats["avg_time_ms"] = (stats["total_time_s"] * 1000) / stats["total_records"] if stats["total_records"] > 0 else 0
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("Processing Complete")
    logger.info("=" * 60)
    logger.info(f"Total records: {stats['total_records']}")
    logger.info(f"Successful: {stats['successful']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Total time: {stats['total_time_s']:.2f}s")
    logger.info(f"Average time: {stats['avg_time_ms']:.1f}ms/record")
    logger.info(f"Processing rate: {stats['total_records'] / stats['total_time_s']:.1f} records/s")
    logger.info(f"✓ Results written to: {output_path}")
    logger.info("=" * 60)
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced Evo2 Service - Real Feature Extraction',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process JSONL dataset with Evo2 features
  python app_enhanced.py \\
    --input /data/converted/merged_dataset.jsonl \\
    --output /data/output/evo2/features.json \\
    --mode features
  
  # Process with limit (for testing)
  python app_enhanced.py \\
    --input /data/converted/merged_dataset.jsonl \\
    --output /data/output/evo2/features_test.json \\
    --mode features \\
    --limit 1000
  
  # Use real Evo2 model (if available)
  export USE_EVO2_LM=1
  python app_enhanced.py \\
    --input /data/converted/merged_dataset.jsonl \\
    --output /data/output/evo2/features_real.json \\
    --mode features
        """
    )
    
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input JSONL file path'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output JSON file path (default: auto-generated in /data/output/evo2/)'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['features', 'generate'],
        default='features',
        help='Processing mode (default: features)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of records to process (for testing)'
    )
    
    args = parser.parse_args()
    
    # Load model
    model = load_evo2_model()
    
    # Check input
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = Path('/data/output/evo2')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{input_path.stem}_features.json"
    
    # Process based on mode
    if args.mode == 'features':
        stats = process_jsonl_records(
            input_path=input_path,
            output_path=output_path,
            model=model,
            limit=args.limit
        )
    else:
        logger.error(f"Mode '{args.mode}' not implemented yet")
        sys.exit(1)


if __name__ == '__main__':
    main()


#!/usr/bin/env python3
"""
CodonTransformer Service - Codon Optimization
Processes sequences and optimizes codons for target organisms
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('codon-transformer-service')


def load_codon_transformer():
    """Load CodonTransformer model"""
    try:
        # Add CodonTransformer to path
        import sys
        sys.path.insert(0, '/opt/CodonTransformer')
        
        # Try different import paths
        try:
            from CodonTransformer import load_model
        except ImportError:
            # Alternative import if load_model is in a different location
            import CodonTransformer
            logger.info("CodonTransformer module loaded, model loading will be done on-demand")
            return True
        
        logger.info("Loading CodonTransformer model...")
        model = load_model()
        logger.info("✓ CodonTransformer model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to load CodonTransformer: {e}")
        raise


def process_task(task_data: Dict[str, Any], model) -> Dict[str, Any]:
    """Process a single optimization task"""
    start_time = time.time()
    
    try:
        task_type = task_data.get('task', 'optimize')
        input_data = task_data.get('input', {})
        
        sequence = input_data.get('sequence', '')
        organism = input_data.get('organism', 'human')
        parameters = input_data.get('parameters', {})
        
        logger.info(f"Optimizing sequence for: {organism}")
        
        # TODO: Implement actual CodonTransformer inference
        # This is a placeholder
        result = {
            "task": task_type,
            "status": "success",
            "output": {
                "optimized_sequence": sequence + "_OPTIMIZED",
                "cai_score": 0.85,
                "gc_content": 0.52,
                "organism": organism
            },
            "metadata": {
                "request_id": task_data.get('metadata', {}).get('request_id', 'unknown'),
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "service": "codon_transformer",
                "version": "1.0.0"
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing task: {e}")
        return {
            "task": task_data.get('task', 'unknown'),
            "status": "error",
            "error": str(e),
            "metadata": {
                "request_id": task_data.get('metadata', {}).get('request_id', 'unknown'),
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "service": "codon_transformer",
                "version": "1.0.0"
            }
        }


def main():
    parser = argparse.ArgumentParser(description='CodonTransformer Service')
    parser.add_argument('--input', type=str, required=True,
                       help='Input JSON file path')
    parser.add_argument('--output', type=str,
                       help='Output JSON file path')
    parser.add_argument('--batch', action='store_true',
                       help='Process multiple tasks')
    
    args = parser.parse_args()
    
    model = load_codon_transformer()
    
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    with open(input_path, 'r') as f:
        input_data = json.load(f)
    
    # Auto-detect batch mode based on input data structure
    if isinstance(input_data, list):
        logger.info(f"Processing {len(input_data)} tasks in batch mode")
        results = [process_task(task, model) for task in input_data]
    else:
        logger.info("Processing single task")
        results = process_task(input_data, model)
    
    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = Path('/data/output/codon_transformer')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{input_path.stem}_result.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"✓ Results written to: {output_path}")


if __name__ == '__main__':
    main()


#!/usr/bin/env python3
"""
Batch Processing Script for Codon Verifier Microservices

Processes multiple input files in parallel using Docker services.
"""

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('batch-processor')


class ServiceRunner:
    """Run Docker services for batch processing"""
    
    SERVICES = {
        'evo2': 'codon-verifier/evo2:latest',
        'codon_transformer': 'codon-verifier/codon-transformer:latest',
        'codon_verifier': 'codon-verifier/codon-verifier:latest'
    }
    
    def __init__(self, service_name: str, data_dir: Path):
        if service_name not in self.SERVICES:
            raise ValueError(f"Unknown service: {service_name}")
        
        self.service_name = service_name
        self.image = self.SERVICES[service_name]
        self.data_dir = data_dir
    
    def process_file(self, input_file: Path) -> Dict[str, Any]:
        """Process a single file using Docker service"""
        try:
            start_time = time.time()
            
            # Prepare Docker command
            cmd = [
                'docker', 'run', '--rm',
                '-v', f'{self.data_dir.absolute()}:/data',
                self.image,
                '--input', f'/data/input/{input_file.name}'
            ]
            
            logger.info(f"Processing {input_file.name} with {self.service_name}")
            
            # Run Docker container
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                elapsed = time.time() - start_time
                logger.info(f"✓ {input_file.name} completed in {elapsed:.2f}s")
                return {
                    'file': input_file.name,
                    'status': 'success',
                    'elapsed_time': elapsed
                }
            else:
                logger.error(f"✗ {input_file.name} failed: {result.stderr}")
                return {
                    'file': input_file.name,
                    'status': 'error',
                    'error': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            logger.error(f"✗ {input_file.name} timed out")
            return {
                'file': input_file.name,
                'status': 'timeout'
            }
        except Exception as e:
            logger.error(f"✗ {input_file.name} error: {e}")
            return {
                'file': input_file.name,
                'status': 'error',
                'error': str(e)
            }


def find_input_files(input_dir: Path, pattern: str = '*.json') -> List[Path]:
    """Find all input files matching pattern"""
    return list(input_dir.glob(pattern))


def batch_process(service_name: str, input_dir: Path, workers: int = 4) -> List[Dict[str, Any]]:
    """Process multiple files in parallel"""
    data_dir = input_dir.parent
    runner = ServiceRunner(service_name, data_dir)
    
    input_files = find_input_files(input_dir)
    if not input_files:
        logger.warning(f"No input files found in {input_dir}")
        return []
    
    logger.info(f"Found {len(input_files)} files to process")
    logger.info(f"Using {workers} parallel workers")
    
    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(runner.process_file, f): f 
            for f in input_files
        }
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
    
    return results


def print_summary(results: List[Dict[str, Any]]):
    """Print processing summary"""
    total = len(results)
    success = sum(1 for r in results if r['status'] == 'success')
    failed = total - success
    
    logger.info("=" * 60)
    logger.info("BATCH PROCESSING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total files:     {total}")
    logger.info(f"Successful:      {success}")
    logger.info(f"Failed/Timeout:  {failed}")
    
    if success > 0:
        avg_time = sum(r.get('elapsed_time', 0) for r in results if r['status'] == 'success') / success
        logger.info(f"Average time:    {avg_time:.2f}s")
    
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Batch process files using Codon Verifier microservices'
    )
    parser.add_argument(
        '--service',
        required=True,
        choices=['evo2', 'codon_transformer', 'codon_verifier'],
        help='Service to use for processing'
    )
    parser.add_argument(
        '--input-dir',
        type=Path,
        default=Path('./data/input'),
        help='Input directory containing JSON files'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Number of parallel workers'
    )
    parser.add_argument(
        '--pattern',
        default='*.json',
        help='File pattern to match (default: *.json)'
    )
    
    args = parser.parse_args()
    
    if not args.input_dir.exists():
        logger.error(f"Input directory not found: {args.input_dir}")
        sys.exit(1)
    
    # Run batch processing
    results = batch_process(args.service, args.input_dir, args.workers)
    
    # Print summary
    print_summary(results)
    
    # Save results
    output_file = Path('./logs') / f'batch_{args.service}_{int(time.time())}.json'
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Detailed results saved to: {output_file}")


if __name__ == '__main__':
    main()


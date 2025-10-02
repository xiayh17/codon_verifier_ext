#!/usr/bin/env python3
"""
Sequential Pipeline Script

Chains multiple services together in a pipeline:
Input -> Evo2 -> CodonTransformer -> CodonVerifier -> Output
"""

import argparse
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pipeline')


class Pipeline:
    """Sequential processing pipeline"""
    
    # Map service names to Docker image names
    SERVICE_IMAGE_MAP = {
        'evo2': 'evo2',
        'codon_transformer': 'codon-transformer',
        'codon_verifier': 'codon-verifier'
    }
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.temp_dir = data_dir / 'temp'
        self.temp_dir.mkdir(exist_ok=True)
    
    def run_service(self, service: str, input_file: Path) -> Path:
        """Run a single service and return output file path"""
        logger.info(f"Running {service} on {input_file.name}")
        
        output_file = self.temp_dir / f"{service}_{input_file.stem}_output.json"
        
        # Calculate relative path from data_dir to input_file
        try:
            rel_path = input_file.absolute().relative_to(self.data_dir.absolute())
            container_input_path = f'/data/{rel_path}'
        except ValueError:
            # If input_file is not under data_dir, just use the filename
            container_input_path = f'/data/input/{input_file.name}'
        
        # Get correct image name from mapping
        image_name = self.SERVICE_IMAGE_MAP.get(service, service)
        
        cmd = [
            'docker', 'run', '--rm',
            '-v', f'{self.data_dir.absolute()}:/data',
            f'codon-verifier/{image_name}:latest',
            '--input', container_input_path,
            '--output', f'/data/temp/{output_file.name}'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"✓ {service} completed")
                return output_file
            else:
                logger.error(f"✗ {service} failed: {result.stderr}")
                raise RuntimeError(f"{service} failed")
                
        except subprocess.TimeoutExpired:
            logger.error(f"✗ {service} timed out")
            raise RuntimeError(f"{service} timed out")
    
    def run_full_pipeline(self, input_file: Path) -> Dict[str, Any]:
        """Run complete pipeline on input file"""
        start_time = time.time()
        
        try:
            # Stage 1: Evo2
            logger.info("=" * 60)
            logger.info(f"Starting pipeline for: {input_file.name}")
            logger.info("=" * 60)
            
            stage1_output = self.run_service('evo2', input_file)
            
            # Stage 2: CodonTransformer
            stage2_output = self.run_service('codon_transformer', stage1_output)
            
            # Stage 3: CodonVerifier
            stage3_output = self.run_service('codon_verifier', stage2_output)
            
            # Copy final output
            final_output = self.data_dir / 'output' / f'pipeline_{input_file.stem}_final.json'
            final_output.parent.mkdir(exist_ok=True)
            
            with open(stage3_output, 'r') as f:
                final_data = json.load(f)
            
            with open(final_output, 'w') as f:
                json.dump(final_data, f, indent=2)
            
            elapsed = time.time() - start_time
            
            logger.info("=" * 60)
            logger.info(f"✓ Pipeline completed in {elapsed:.2f}s")
            logger.info(f"Final output: {final_output}")
            logger.info("=" * 60)
            
            return {
                'status': 'success',
                'input_file': str(input_file),
                'output_file': str(final_output),
                'elapsed_time': elapsed
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {
                'status': 'error',
                'input_file': str(input_file),
                'error': str(e)
            }


def main():
    parser = argparse.ArgumentParser(
        description='Run sequential pipeline: Evo2 -> CodonTransformer -> CodonVerifier'
    )
    parser.add_argument(
        '--input',
        type=Path,
        required=True,
        help='Input JSON file'
    )
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=Path('./data'),
        help='Data directory (default: ./data)'
    )
    
    args = parser.parse_args()
    
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return 1
    
    # Ensure paths are absolute
    data_dir = args.data_dir.absolute()
    input_file = args.input.absolute()
    
    pipeline = Pipeline(data_dir)
    result = pipeline.run_full_pipeline(input_file)
    
    if result['status'] == 'success':
        return 0
    else:
        return 1


if __name__ == '__main__':
    exit(main())


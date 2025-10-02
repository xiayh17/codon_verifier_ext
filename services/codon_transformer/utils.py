"""Utility functions for CodonTransformer service"""

import json
from pathlib import Path
from typing import Dict, Any, List


def validate_input(data: Dict[str, Any]) -> bool:
    """Validate input JSON structure"""
    required_fields = ['task', 'input']
    if not all(field in data for field in required_fields):
        return False
    
    input_data = data['input']
    return 'sequence' in input_data


def parse_organism(organism_str: str) -> str:
    """Parse and validate organism name"""
    valid_organisms = [
        'human', 'mouse', 'ecoli', 'yeast', 
        'drosophila', 'celegans', 'zebrafish'
    ]
    
    organism_lower = organism_str.lower()
    if organism_lower in valid_organisms:
        return organism_lower
    else:
        return 'human'  # default


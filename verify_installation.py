#!/usr/bin/env python
"""
Quick verification script to test all components in the Docker environment
"""

import sys
from typing import Tuple

def test_component(name: str, test_func) -> Tuple[bool, str]:
    """Test a component and return success status and message"""
    try:
        result = test_func()
        return True, result
    except Exception as e:
        return False, str(e)

def test_python():
    """Test Python version"""
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    assert sys.version_info >= (3, 8), "Python 3.8+ required"
    return f"Python {version}"

def test_pytorch():
    """Test PyTorch and CUDA"""
    import torch
    cuda_available = torch.cuda.is_available()
    cuda_version = torch.version.cuda if cuda_available else "N/A"
    gpu_count = torch.cuda.device_count() if cuda_available else 0
    
    info = f"PyTorch {torch.__version__}, CUDA: {cuda_available}"
    if cuda_available:
        info += f", CUDA version: {cuda_version}, GPUs: {gpu_count}"
        if gpu_count > 0:
            info += f", GPU 0: {torch.cuda.get_device_name(0)}"
    return info

def test_numpy():
    """Test NumPy"""
    import numpy as np
    return f"NumPy {np.__version__}"

def test_sklearn():
    """Test scikit-learn"""
    import sklearn
    return f"scikit-learn {sklearn.__version__}"

def test_lightgbm():
    """Test LightGBM"""
    import lightgbm as lgb
    return f"LightGBM {lgb.__version__}"

def test_evo2():
    """Test Evo2"""
    import evo2
    # Try to get version if available
    version = getattr(evo2, '__version__', 'installed')
    return f"Evo2 {version}"

def test_codontransformer():
    """Test CodonTransformer"""
    from CodonTransformer import DNA2PROTEIN
    return "CodonTransformer: DNA2PROTEIN loaded"

def test_viennarna_python():
    """Test ViennaRNA Python bindings"""
    import RNA
    version = RNA.version()
    return f"ViennaRNA Python: {version}"

def test_viennarna_cli():
    """Test ViennaRNA CLI tools"""
    import subprocess
    result = subprocess.run(['RNAfold', '--version'], 
                          capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        version_line = result.stdout.split('\n')[0]
        return f"ViennaRNA CLI: {version_line}"
    raise Exception("RNAfold not found or failed")

def test_codon_verifier():
    """Test Codon Verifier framework"""
    from codon_verifier import generator, surrogate, reward
    from codon_verifier.hosts.tables import E_COLI_USAGE
    
    # Quick sanity check
    assert len(E_COLI_USAGE) > 0, "E. coli codon usage table is empty"
    return "Codon Verifier: core modules loaded"

def test_biopython():
    """Test Biopython"""
    import Bio
    return f"Biopython {Bio.__version__}"

def test_transformers():
    """Test HuggingFace Transformers"""
    import transformers
    return f"Transformers {transformers.__version__}"

def main():
    """Run all verification tests"""
    print("=" * 70)
    print("Codon Verifier Docker Environment Verification")
    print("=" * 70)
    print()
    
    tests = [
        ("Python", test_python),
        ("PyTorch & CUDA", test_pytorch),
        ("NumPy", test_numpy),
        ("scikit-learn", test_sklearn),
        ("LightGBM", test_lightgbm),
        ("Evo2", test_evo2),
        ("CodonTransformer", test_codontransformer),
        ("ViennaRNA (Python)", test_viennarna_python),
        ("ViennaRNA (CLI)", test_viennarna_cli),
        ("Biopython", test_biopython),
        ("Transformers", test_transformers),
        ("Codon Verifier", test_codon_verifier),
    ]
    
    results = []
    max_name_len = max(len(name) for name, _ in tests)
    
    for name, test_func in tests:
        success, message = test_component(name, test_func)
        results.append((name, success, message))
        
        status = "✓" if success else "✗"
        padding = " " * (max_name_len - len(name))
        
        if success:
            print(f"  {status} {name}{padding}  {message}")
        else:
            print(f"  {status} {name}{padding}  FAILED: {message}")
    
    print()
    print("=" * 70)
    
    # Summary
    total = len(results)
    passed = sum(1 for _, success, _ in results if success)
    failed = total - passed
    
    print(f"Summary: {passed}/{total} tests passed")
    
    if failed > 0:
        print(f"\nFailed components ({failed}):")
        for name, success, message in results:
            if not success:
                print(f"  - {name}: {message}")
        return 1
    else:
        print("\n✓ All components verified successfully!")
        print("\nYou can now:")
        print("  - Run demo: python codon_verifier/run_demo.py")
        print("  - Train surrogate: python codon_verifier/train_surrogate.py --data toy_dataset.jsonl")
        print("  - Start JupyterLab: jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root")
        return 0

if __name__ == "__main__":
    sys.exit(main())

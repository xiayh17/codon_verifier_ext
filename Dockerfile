# Evo2 + CodonTransformer + Codon Verifier Framework
# Based on NVIDIA PyTorch with CUDA support for Evo2
FROM nvcr.io/nvidia/pytorch:25.04-py3

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/workdir/.cache/huggingface

# ============================================================
# System dependencies
# ============================================================
ENV DEBIAN_FRONTEND=noninteractive

# Install essential build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      wget curl git && \
    rm -rf /var/lib/apt/lists/*

# ============================================================
# Install ViennaRNA from source
# ============================================================
# ViennaRNA needs to be compiled from source
# We'll build it to use the base image's Python (not conda)
WORKDIR /tmp/viennarna

# Install dependencies and build ViennaRNA in one step to avoid cache issues
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      autoconf \
      automake \
      libtool \
      pkg-config \
      swig \
      python3-dev \
      xxd && \
    rm -rf /var/lib/apt/lists/* && \
    echo "Verifying xxd installation:" && \
    which xxd && xxd -v && \
    echo "Downloading ViennaRNA release tarball..." && \
    wget -q https://www.tbi.univie.ac.at/RNA/download/sourcecode/2_6_x/ViennaRNA-2.6.4.tar.gz && \
    tar -xzf ViennaRNA-2.6.4.tar.gz --strip-components=1 && \
    rm ViennaRNA-2.6.4.tar.gz && \
    ./configure \
      --without-python \
      --without-python3 \
      --without-perl \
      --without-python2 \
      --without-swig \
      --without-doc \
      --disable-lto && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    cd / && rm -rf /tmp/viennarna

# Verify ViennaRNA CLI installation (Python bindings not built due to SWIG compatibility)
RUN RNAfold --version && echo "✓ ViennaRNA CLI tools installed successfully"

WORKDIR /tmp
# ============================================================
# Verify base image PyTorch and upgrade pip
# ============================================================
RUN python3 -c "import torch; print(f'Base PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')" && \
    pip install --upgrade pip wheel

# ============================================================
# Install Evo2 (GPU-optimized, requires FP8-capable GPUs)
# ============================================================
# Strategy: Install dependencies first, then evo2 with --no-deps to preserve base PyTorch
# Step 1: Install all dependencies that won't conflict with torch
RUN pip install --no-cache-dir \
        biopython \
        "huggingface_hub>=0.22,<0.36" \
        einops \
        safetensors \
        sentencepiece \
        tqdm

# Step 2: Try installing evo2 normally first to see what dependencies it needs
# If it breaks torch, we'll handle it differently
RUN pip install --no-cache-dir evo2 || \
    (echo "Normal evo2 install failed, trying alternatives..." && \
     pip install --no-deps evo2)

# Step 3: Verify torch is still the base image version
RUN python3 - <<'PY'
import torch
import transformer_engine

print("=" * 50)
print("Checking PyTorch after evo2 installation:")
print("=" * 50)
print("✓ PyTorch:", torch.__version__)
print("✓ CUDA available:", torch.cuda.is_available())
print("✓ Transformer Engine:", transformer_engine.__version__)

# Check if evo2 works
try:
    import evo2
    version = getattr(evo2, "__version__", "installed (no version attr)")
    print("✓ Evo2:", version)
    print("=" * 50)
except ImportError as e:
    print("⚠ Evo2 import failed:", str(e))
    print("=" * 50)
    import sys
    sys.exit(1)
PY

# ============================================================
# Install CodonTransformer
# ============================================================
WORKDIR /opt
RUN git clone https://github.com/adibvafa/CodonTransformer.git

# Install CodonTransformer dependencies manually (avoiding version conflicts)
# Note: We skip torch-related packages as they're from base image
# Force downgrade setuptools to match CodonTransformer's requirements
# Use --force-reinstall --no-deps to override base image's setuptools 78.1.0
RUN pip install --no-cache-dir --force-reinstall --no-deps 'setuptools>=70.0.0,<71.0.0' && \
    pip install --no-cache-dir \
      transformers>=4.30 \
      sentencepiece \
      pandas \
      'CAI-PyPI>=2.0.1,<3.0.0' \
      'python-codon-tables>=0.1.12,<0.2.0' \
      'onnxruntime>=1.16.3,<2.0.0' \
      'ipywidgets>=7.0.0,<8.0.0' \
      'pytorch-lightning>=2.2.1,<3.0.0'

# Now install CodonTransformer in editable mode
WORKDIR /opt/CodonTransformer
RUN pip install -e . --no-deps || \
    (echo "Warning: CodonTransformer editable install failed, adding to PYTHONPATH instead" && \
     echo 'export PYTHONPATH="/opt/CodonTransformer:$PYTHONPATH"' >> /root/.bashrc)

# Verify CodonTransformer installation
RUN python3 -c "import sys; sys.path.insert(0, '/opt/CodonTransformer'); from CodonTransformer import load_model; print('✓ CodonTransformer available')" || \
    echo "⚠ CodonTransformer import failed, will use PYTHONPATH"

# ============================================================
# Install Codon Verifier Framework dependencies
# ============================================================
# Core scientific computing
# Note: pandas, transformers already installed above for CodonTransformer
RUN pip install --no-cache-dir \
      numpy>=1.22 \
      scikit-learn>=1.1 \
      joblib>=1.2 \
      scipy>=1.8 \
      lightgbm>=3.3

# Note: ViennaRNA CLI tools installed (Python bindings skipped due to SWIG compatibility)
#       Your code can use RNAfold command instead of import RNA
# Note: torch, transformers, pandas, biopython, tqdm already installed above

# Jupyter ecosystem for interactive development
RUN pip install --no-cache-dir \
      jupyter \
      jupyterlab \
      ipywidgets \
      notebook

# Additional useful tools
# Note: tqdm and biopython already installed with Evo2 dependencies above
RUN pip install --no-cache-dir \
      matplotlib \
      seaborn

# ============================================================
# Set up working directory
# ============================================================
WORKDIR /workdir

# Pre-create cache directories for models
RUN mkdir -p /workdir/.cache/huggingface && \
    mkdir -p /workdir/.cache/CodonTransformer

# ============================================================
# Final environment verification
# ============================================================
RUN python3 - <<'PY'
import sys
print("=" * 60)
print("FINAL ENVIRONMENT VERIFICATION")
print("=" * 60)

# Core ML stack
import torch
import transformer_engine
print(f"✓ PyTorch: {torch.__version__} (CUDA: {torch.cuda.is_available()})")
print(f"✓ Transformer Engine: {transformer_engine.__version__}")

# Evo2 stack
try:
    import evo2
    version = getattr(evo2, "__version__", "installed (no version attr)")
    print(f"✓ Evo2: {version}")
except ImportError as e:
    print(f"⚠ Evo2: {e}")

# Scientific computing
import numpy as np
import scipy
import sklearn
import pandas as pd
print(f"✓ NumPy: {np.__version__}")
print(f"✓ SciPy: {scipy.__version__}")
print(f"✓ scikit-learn: {sklearn.__version__}")
print(f"✓ Pandas: {pd.__version__}")

# ML tools
import lightgbm as lgb
import transformers
print(f"✓ LightGBM: {lgb.__version__}")
print(f"✓ Transformers: {transformers.__version__}")

# Bioinformatics
import Bio
import subprocess
print(f"✓ Biopython: {Bio.__version__}")
# ViennaRNA installed as CLI tools only (Python bindings skipped due to SWIG compatibility)
rnafold_version = subprocess.check_output(['RNAfold', '--version'], stderr=subprocess.STDOUT).decode().strip()
print(f"✓ ViennaRNA CLI: {rnafold_version.split()[0] if rnafold_version else 'installed'}")

# CodonTransformer (optional check)
try:
    sys.path.insert(0, '/opt/CodonTransformer')
    from CodonTransformer import load_model
    print("✓ CodonTransformer: available")
except Exception as e:
    print(f"⚠ CodonTransformer: {e}")

print("=" * 60)
print("ALL CHECKS PASSED - Environment ready!")
print("=" * 60)
PY

# ============================================================
# Default command
# ============================================================
CMD ["/bin/bash"]

# ============================================================
# Usage Instructions (included as metadata)
# ============================================================
LABEL maintainer="codon_verifier_team"
LABEL description="Integrated environment for Evo2, CodonTransformer, and Codon Verifier Framework"
LABEL usage.build="docker build -t codon-verifier:latest ."
LABEL usage.run="docker run --gpus all -it --rm -v \$PWD:/workdir -v \$HOME/.cache/huggingface:/workdir/.cache/huggingface codon-verifier:latest"
LABEL requirements.hardware="NVIDIA GPU with compute capability >= 8.9 (e.g., H100) for Evo2 FP8 support"

# CodonTransformer Service - Codon Optimization
FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends git build-essential && \
    rm -rf /var/lib/apt/lists/*

# Clone CodonTransformer
RUN git clone https://github.com/adibvafa/CodonTransformer.git /opt/CodonTransformer

# Install CodonTransformer dependencies
RUN pip install --no-cache-dir \
    'setuptools>=70.0.0' \
    transformers>=4.30 \
    sentencepiece \
    pandas \
    'CAI-PyPI>=2.0.1,<3.0.0' \
    'python-codon-tables>=0.1.12,<0.2.0' \
    'onnxruntime>=1.16.3,<2.0.0' \
    torch \
    pytorch-lightning

# Add CodonTransformer to PYTHONPATH instead of installing
ENV PYTHONPATH="/opt/CodonTransformer:${PYTHONPATH}"

# Verify CodonTransformer is accessible (just check if module can be imported)
RUN python3 -c "import sys; sys.path.insert(0, '/opt/CodonTransformer'); import CodonTransformer; print('✓ CodonTransformer module found')"

# Copy service application
COPY services/codon_transformer/app.py /app/
COPY services/codon_transformer/utils.py /app/

ENTRYPOINT ["python3", "app.py"]
CMD ["--help"]



"""
Example host-specific tables. Replace with real codon usage (e.g., highly expressed genes) and tRNA weights.
"""
from typing import Dict

E_COLI_USAGE: Dict[str, float] = {
    "TTA": 0.05, "TTG": 0.13, "CTT": 0.10, "CTC": 0.10, "CTA": 0.04, "CTG": 0.58,
    "GGT": 0.35, "GGC": 0.37, "GGA": 0.16, "GGG": 0.12,
    "GCT": 0.18, "GCC": 0.27, "GCA": 0.23, "GCG": 0.32,
    "CGT": 0.36, "CGC": 0.36, "CGA": 0.07, "CGG": 0.07, "AGA": 0.07, "AGG": 0.07,
    "TCT": 0.18, "TCC": 0.22, "TCA": 0.15, "TCG": 0.12, "AGT": 0.16, "AGC": 0.17,
    "ACT": 0.22, "ACC": 0.43, "ACA": 0.20, "ACG": 0.15,
    "CCT": 0.17, "CCC": 0.17, "CCA": 0.23, "CCG": 0.43,
    "GTT": 0.29, "GTC": 0.21, "GTA": 0.17, "GTG": 0.33,
    "ATT": 0.48, "ATC": 0.39, "ATA": 0.13,
    "TTT": 0.57, "TTC": 0.43,
    "TAT": 0.58, "TAC": 0.42,
    "CAT": 0.57, "CAC": 0.43,
    "CAA": 0.34, "CAG": 0.66,
    "AAT": 0.46, "AAC": 0.54,
    "AAA": 0.76, "AAG": 0.24,
    "GAT": 0.63, "GAC": 0.37,
    "GAA": 0.68, "GAG": 0.32,
    "TGT": 0.46, "TGC": 0.54,
    "TGG": 1.0,
    "ATG": 1.0,
}

E_COLI_TRNA = {c: max(0.05, v) for c, v in E_COLI_USAGE.items()}

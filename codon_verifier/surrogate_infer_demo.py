
"""
Inference demo: load a trained surrogate model and predict mu, sigma for sequences.
"""
import argparse, json, sys
from codon_verifier.surrogate import load_and_predict
from codon_verifier.hosts.tables import E_COLI_USAGE, E_COLI_TRNA

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="Path to trained model .pkl")
    ap.add_argument("--seq", nargs="+", required=True, help="DNA coding sequences (no terminal stop)")
    args = ap.parse_args()

    usage, trna = E_COLI_USAGE, E_COLI_TRNA
    preds = load_and_predict(args.model, args.seq, usage, trna_w=trna, extra=None)
    print(json.dumps(preds, indent=2))

if __name__ == "__main__":
    main()

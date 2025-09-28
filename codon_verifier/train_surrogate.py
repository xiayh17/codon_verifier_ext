
"""
Train the surrogate model from a JSONL dataset and save to a .pkl.
Each JSONL line should match the schema discussed earlier:
{
  "sequence": "ATG...",
  "protein_aa": "M...",
  "host": "E_coli",
  "expression": {"value": 123.4, "unit": "RFU", "assay": "bulk_fluor"},
  "extra_features": {...}  # optional
}
"""
import argparse, json, os
from codon_verifier.surrogate import train_and_save
from codon_verifier.hosts.tables import E_COLI_USAGE, E_COLI_TRNA

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="Path to JSONL dataset")
    ap.add_argument("--out", required=True, help="Output model path (.pkl)")
    ap.add_argument("--host", default="E_coli", help="Host selector (demo uses E. coli tables)")
    args = ap.parse_args()

    # For demo, we only wire E. coli; extend with your own host switch
    usage, trna = E_COLI_USAGE, E_COLI_TRNA

    metrics = train_and_save(args.data, usage, trna, args.out)
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()

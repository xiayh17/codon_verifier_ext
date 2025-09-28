from __future__ import annotations
import argparse, json
from typing import List

from codon_verifier.metrics import rules_score
from codon_verifier.hosts.tables import E_COLI_USAGE, E_COLI_TRNA


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dna", nargs="+", required=True, help="DNA sequences to evaluate")
    ap.add_argument("--motif", action="append", default=["GAATTC","GGATCC"], help="Forbidden motifs")
    args = ap.parse_args()

    usage, trna = E_COLI_USAGE, E_COLI_TRNA
    motifs = list(args.motif) if args.motif else []

    results: List[dict] = []
    for seq in args.dna:
        rs = rules_score(
            seq, usage, trna_w=trna, cpb=None, motifs=motifs,
            diversity_refs=[], use_vienna_dG=True
        )
        out = {"dna": seq}
        out.update(rs)
        results.append(out)

    # Aggregate summary
    n = len(results)
    viol = sum(1 for r in results if r.get("forbidden_hits", 0) > 0)
    avg_cai = sum(r.get("cai", 0.0) for r in results)/n if n else 0.0
    avg_gc = sum(r.get("gc", 0.0) for r in results)/n if n else 0.0
    print(json.dumps({
        "summary": {"n": n, "forbidden_violation_rate": viol/max(1,n), "avg_cai": avg_cai, "avg_gc": avg_gc},
        "results": results
    }, indent=2))

if __name__ == "__main__":
    main()



from __future__ import annotations

"""
CLI to generate candidates in zero-data or small-data modes and score them.

Zero-data: use LM features and rules only (optionally Evo2 if enabled).
Small-data: also load a surrogate .pkl to supply (mu, sigma).
"""

import argparse, json
from typing import List

from .generator import generate_candidates
from .hosts.tables import E_COLI_USAGE, E_COLI_TRNA
from .lm_features import combined_lm_features
from .reward import combine_reward
from .surrogate import load_and_predict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aa", required=True, help="Protein AA sequence (no stop)")
    ap.add_argument("--host", default="E_coli", help="Host name")
    ap.add_argument("--n", type=int, default=100, help="Number of candidates to return")
    ap.add_argument("--source", choices=["ct","policy","heuristic"], default="heuristic")
    ap.add_argument("--method", default="transformer", help="ct method: transformer|HFC|BFC|URC")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--topk", type=int, default=50)
    ap.add_argument("--beams", type=int, default=0)
    ap.add_argument("--forbid", nargs="*", default=["GAATTC","GGATCC"], help="Forbidden motifs")
    ap.add_argument("--surrogate", default=None, help="Path to surrogate .pkl (small-data mode)")
    ap.add_argument("--top", type=int, default=50, help="Top-K to print after scoring")
    args = ap.parse_args()

    # For demo purposes we use the E. coli tables. Extend to your hosts as needed.
    usage, trna = E_COLI_USAGE, E_COLI_TRNA

    cands = generate_candidates(
        aa=args.aa, host=args.host, n=args.n, source=args.source,
        motifs_forbidden=args.forbid, temperature=args.temperature,
        top_k=args.topk, beam_size=args.beams, method=args.method,
    )

    results = []
    # Small-data? get mu/sigma via surrogate
    musig = None
    if args.surrogate:
        preds = load_and_predict(args.surrogate, cands, usage, trna_w=trna, extra=None)
        musig = [(p["mu"], p["sigma"]) for p in preds]

    for i, dna in enumerate(cands):
        lm_feats = combined_lm_features(dna, aa=args.aa, host=args.host)
        mu = sigma = None
        if musig is not None:
            mu, sigma = musig[i]
        res = combine_reward(
            dna=dna,
            usage=usage,
            surrogate_mu=mu,
            surrogate_sigma=sigma,
            trna_w=trna,
            cpb=None,
            motifs=args.forbid,
            lm_features=lm_feats,
            extra_features=dict(lm_feats),
            w_surrogate=1.0,
            w_rules=1.0,
            lambda_uncertainty=1.0,
        )
        results.append({
            "dna": dna,
            "reward": res.get("reward", 0.0),
            **{k: v for k, v in res.items() if k != "lm_features" and k != "extra_features"}
        })

    results.sort(key=lambda x: x["reward"], reverse=True)
    print(json.dumps(results[:args.top], indent=2))


if __name__ == "__main__":
    main()



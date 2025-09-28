from __future__ import annotations
import argparse, json, random
from typing import List

from codon_verifier.policy import HostConditionalCodonPolicy
from codon_verifier.reward import combine_reward
from codon_verifier.features import assemble_feature_bundle
from codon_verifier.hosts.tables import E_COLI_USAGE, E_COLI_TRNA


def group_relative_advantages(rewards: List[float]) -> List[float]:
    m = sum(rewards)/len(rewards) if rewards else 0.0
    std = (sum((r-m)**2 for r in rewards)/len(rewards))**0.5 if rewards else 1.0
    std = max(1e-6, std)
    return [(r - m)/std for r in rewards]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aa", required=True, help="Protein amino-acid sequence")
    ap.add_argument("--host", default="E_coli", help="Host key (demo: E_coli)")
    ap.add_argument("--groups", type=int, default=8, help="Group size per GRPO step")
    ap.add_argument("--steps", type=int, default=50, help="Number of training steps")
    ap.add_argument("--temperature", type=float, default=1.0, help="Sampling temperature")
    ap.add_argument("--motif", action="append", default=["GAATTC","GGATCC"], help="Forbidden motifs")
    ap.add_argument("--w_rules", type=float, default=1.0)
    ap.add_argument("--w_sur", type=float, default=1.0)
    ap.add_argument("--lambda_unc", type=float, default=1.0)
    args = ap.parse_args()

    # Initialize policy and reference
    policy = HostConditionalCodonPolicy([args.host], init_usage=E_COLI_USAGE)
    ref_policy = policy.clone()

    aa = args.aa
    motifs = list(args.motif) if args.motif else []
    usage, trna = E_COLI_USAGE, E_COLI_TRNA
    fb = assemble_feature_bundle(aa)
    extra = fb.to_dict()

    for step in range(args.steps):
        # Sample a group of candidates
        samples = []
        for _ in range(args.groups):
            dna, logp = policy.sample_sequence(aa, args.host, motifs_forbidden=motifs, temperature=args.temperature)
            # Note: surrogate model not wired here; using placeholder mu/sigma
            res = combine_reward(
                dna=dna,
                usage=usage,
                surrogate_mu=0.0,
                surrogate_sigma=0.0,
                trna_w=trna,
                cpb=None,
                motifs=motifs,
                extra_features=extra,
                w_surrogate=args.w_sur,
                w_rules=args.w_rules,
                lambda_uncertainty=args.lambda_unc,
                enforce_hard_constraints=True,
            )
            samples.append((dna, logp, res["reward"]))

        advs = group_relative_advantages([r for _,_,r in samples])
        # Prepare chosen codon lists per sample
        chosen_lists: List[List[str]] = []
        for dna, _, _ in samples:
            chosen_lists.append([dna[i:i+3] for i in range(0, len(dna), 3)])

        # Update policy
        policy.update_from_samples(
            host=args.host,
            aa_seqs=[aa]*len(samples),
            chosen_codons=chosen_lists,
            advantages=advs,
            ref_policy=ref_policy,
            lr=0.05,
            beta_ref=0.01,
        )

        if (step+1) % 10 == 0:
            # Refresh reference policy periodically
            ref_policy = policy.clone()

        best = max(samples, key=lambda x: x[2])
        print(json.dumps({
            "step": step+1,
            "best_reward": best[2],
            "best_dna": best[0],
            "mean_reward": sum(r for _,_,r in samples)/len(samples)
        }))

if __name__ == "__main__":
    main()



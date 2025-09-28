
from typing import Dict, Optional, List
from .metrics import rules_score, find_forbidden_sites

def combine_reward(
    dna: str,
    usage: Dict[str,float],
    surrogate_mu: Optional[float] = None,
    surrogate_sigma: Optional[float] = None,
    trna_w: Optional[Dict[str,float]] = None,
    cpb: Optional[Dict[str,float]] = None,
    motifs: Optional[List[str]] = None,
    lm_features: Optional[dict] = None,
    extra_features: Optional[dict] = None,
    weights_rules: Optional[Dict[str,float]] = None,
    w_surrogate: float = 1.0,
    w_rules: float = 1.0,
    lambda_uncertainty: float = 1.0,
    enforce_hard_constraints: bool = True,
    max_forbidden_hits: int = 0,
) -> Dict[str,float]:
    """
    R = w_surrogate * (mu - lambda * sigma) + w_rules * total_rules
    """
    extra_for_rules = dict(extra_features or {})
    if lm_features:
        # expose LM features to downstream consumers (e.g., surrogate training)
        for k, v in lm_features.items():
            if k not in extra_for_rules:
                extra_for_rules[k] = v

    rs = rules_score(
        dna, usage,
        lm_features=lm_features,
        extra_features=extra_for_rules,
        trna_w=trna_w, cpb=cpb, motifs=motifs, weights=weights_rules
    )
    mu = surrogate_mu if surrogate_mu is not None else 0.0
    sig = surrogate_sigma if surrogate_sigma is not None else 0.0
    reward = w_surrogate * (mu - lambda_uncertainty * sig) + w_rules * rs["total_rules"]
    valid = True
    violation_reason = None
    if enforce_hard_constraints and motifs:
        hits = find_forbidden_sites(dna, motifs)
        if len(hits) > max_forbidden_hits:
            valid = False
            violation_reason = "forbidden_motif"
            reward = float("-inf")
    out = {"reward": reward, "surrogate_mu": mu, "surrogate_sigma": sig, "valid": valid}
    if violation_reason:
        out["violation_reason"] = violation_reason
    out.update(rs)
    if lm_features:
        out.setdefault("lm_features", lm_features)
    if extra_features:
        out.setdefault("extra_features", extra_for_rules)
    return out


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
    rs = rules_score(
        dna, usage,
        extra_features=extra_features,
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
    return out

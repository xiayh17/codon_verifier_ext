
from codon_verifier.reward import combine_reward
from codon_verifier.hosts.tables import E_COLI_USAGE, E_COLI_TRNA
from codon_verifier.codon_utils import constrained_decode
from codon_verifier.lm_features import combined_lm_features

dna = constrained_decode("M" + "A"*20, E_COLI_USAGE, motifs_forbidden=["GAATTC","GGATCC"], temperature=0.8)
lm_feats = combined_lm_features(dna, aa="M" + "A"*20, host="E_coli")
res = combine_reward(
    dna=dna,
    usage=E_COLI_USAGE,
    surrogate_mu=0.8,
    surrogate_sigma=0.1,
    trna_w=E_COLI_TRNA,
    cpb=None,
    motifs=["GAATTC","GGATCC"],
    lm_features=lm_feats,
    w_surrogate=1.0, w_rules=1.0, lambda_uncertainty=1.0,
)
for k,v in res.items():
    print(f"{k:>16}: {v}")

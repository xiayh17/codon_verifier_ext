
from codon_verifier.reward import combine_reward
from codon_verifier.hosts.tables import E_COLI_USAGE, E_COLI_TRNA
from codon_verifier.features import assemble_feature_bundle
from codon_verifier.cache import save_features, load_features
from codon_verifier.lm_features import combined_lm_features

aa = "M" + "A"*60
dna = "ATG" + "GCT"*60

fb = assemble_feature_bundle(aa)   # no external files; will compute AA-derived props only
feat_dict = fb.to_dict()
save_features(aa, "E_coli", feat_dict)
cached = load_features(aa, "E_coli")
lm_feats = combined_lm_features(dna, aa=aa, host="E_coli")
merged_extra = dict(cached)
merged_extra.update(lm_feats)

res = combine_reward(
    dna=dna,
    usage=E_COLI_USAGE,
    surrogate_mu=0.6,
    surrogate_sigma=0.05,
    trna_w=E_COLI_TRNA,
    motifs=["GAATTC","GGATCC"],
    lm_features=lm_feats,
    extra_features=merged_extra,
    w_surrogate=1.0, w_rules=1.0, lambda_uncertainty=1.0,
)

print("Extra features:", merged_extra)
for k,v in res.items():
    print(f"{k:>16}: {v}")

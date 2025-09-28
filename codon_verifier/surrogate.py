
from __future__ import annotations
import os, json, math, warnings
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np

try:
    import lightgbm as lgb
    _HAS_LGB = True
except Exception:
    _HAS_LGB = False

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib

from .metrics import (
    gc_content, sliding_gc, rules_score, cai, tai,
    five_prime_structure_proxy, rare_codon_runs, homopolymers, codon_pair_bias_score
)
from .codon_utils import chunk_codons, CODON_TO_AA, AA_TO_CODONS, relative_adaptiveness_from_usage

##############################
# Feature engineering helpers
##############################

def codon_histogram(dna: str) -> Dict[str, float]:
    codons = chunk_codons(dna)
    counts = {}
    total = 0
    for aa, cods in AA_TO_CODONS.items():
        for c in cods:
            counts[c] = 0
    for c in codons:
        if len(c)==3 and all(b in "ACGT" for b in c):
            counts[c] = counts.get(c,0)+1
            total += 1
    if total>0:
        for k in counts.keys():
            counts[k] = counts[k]/total
    return counts

def aggregate_window_gc(seq: str, window: int = 50, step: int = 10) -> Dict[str, float]:
    gcs = sliding_gc(seq, window=window, step=step)
    if not gcs:
        return {"gcw_mean": 0.0, "gcw_std": 0.0, "gcw_min": 0.0, "gcw_max": 0.0}
    arr = np.array(gcs, dtype=float)
    return {
        "gcw_mean": float(arr.mean()),
        "gcw_std": float(arr.std()),
        "gcw_min": float(arr.min()),
        "gcw_max": float(arr.max()),
    }

def extra_feature_defaults(extra: Optional[dict]) -> Dict[str, float]:
    extra = extra or {}
    keys = [
        "plDDT_mean","plDDT_min","esm_emb_dim","esm_emb_l2","msa_depth",
        "conservation_mean","length","kd_hydropathy_mean"
    ]
    out = {k: float(extra.get(k, 0.0) or 0.0) for k in keys}
    # Pass through LM-derived features
    for k, v in extra.items():
        if isinstance(v, (int, float)) and k.startswith("lm_"):
            out[k] = float(v)
    for k in [
        "lm_host_score","lm_host_geom","lm_host_perplexity",
        "lm_cond_score","lm_cond_geom","lm_cond_perplexity"
    ]:
        out.setdefault(k, 0.0)
    return out

def build_feature_vector(
    dna: str,
    usage: Dict[str,float],
    trna_w: Optional[Dict[str,float]] = None,
    cpb: Optional[Dict[str,float]] = None,
    extra_features: Optional[dict] = None
) -> Tuple[np.ndarray, List[str]]:
    # scalar metrics
    f = {}
    f["len_nt"] = len(dna)
    f["gc"] = gc_content(dna)
    win = aggregate_window_gc(dna, window=50, step=10)
    f.update(win)
    try:
        f["cai"] = cai(dna, usage)
    except Exception:
        f["cai"] = 0.0
    if trna_w is not None:
        try:
            f["tai"] = tai(dna, trna_w)
        except Exception:
            f["tai"] = 0.0
    else:
        f["tai"] = 0.0
    f["struct5_proxy"] = five_prime_structure_proxy(dna, window_nt=45)
    runs = rare_codon_runs(dna, usage, quantile=0.2, min_run=3)
    f["rare_run_len"] = float(sum(L for _,L in runs))
    homos = homopolymers(dna, min_len=6)
    f["homopoly_len"] = float(sum(L for _,_,L in homos))
    f["cpb"] = codon_pair_bias_score(dna, cpb) if cpb is not None else 0.0

    # codon histogram (61 dims including ATG/TGG families)
    hist = codon_histogram(dna)
    f.update({f"codon_{k}": v for k,v in hist.items()})

    # extra features
    f.update(extra_feature_defaults(extra_features))

    # to vector
    keys = sorted(f.keys())
    vec = np.array([f[k] for k in keys], dtype=float)
    return vec, keys

########################
# Surrogate model
########################

@dataclass
class SurrogateConfig:
    quantile_hi: float = 0.84   # ~ +1 sigma for normal
    test_size: float = 0.15
    random_state: int = 42

class SurrogateModel:
    """
    Train two regressors:
      - median regressor (mu) at 0.5 quantile (if LightGBM: objective='quantile' alpha=0.5)
      - upper quantile regressor (q_hi) at alpha=quantile_hi
    Then sigma approx = max(1e-6, q_hi - mu).
    If LightGBM isn't available, uses sklearn.ensemble.GradientBoostingRegressor with loss='quantile'.
    """
    def __init__(self, feature_keys: Optional[List[str]] = None, cfg: Optional[SurrogateConfig] = None):
        self.feature_keys = feature_keys or []
        self.cfg = cfg or SurrogateConfig()
        self.mu_model = None
        self.hi_model = None
        self.scaler = StandardScaler()

    def _make_lgb(self, alpha: float):
        params = dict(objective="quantile", alpha=alpha, n_estimators=400, learning_rate=0.05)
        return lgb.LGBMRegressor(**params)

    def _make_gbr(self, alpha: float):
        return GradientBoostingRegressor(loss="quantile", alpha=alpha, n_estimators=400, learning_rate=0.05, max_depth=3)

    def fit(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        # standardize features
        Xs = self.scaler.fit_transform(X)
        if _HAS_LGB:
            self.mu_model = self._make_lgb(0.5)
            self.hi_model = self._make_lgb(self.cfg.quantile_hi)
        else:
            self.mu_model = self._make_gbr(0.5)
            self.hi_model = self._make_gbr(self.cfg.quantile_hi)

        Xtr, Xte, ytr, yte = train_test_split(Xs, y, test_size=self.cfg.test_size, random_state=self.cfg.random_state)
        self.mu_model.fit(Xtr, ytr)
        self.hi_model.fit(Xtr, ytr)

        mu_pred = self.mu_model.predict(Xte)
        hi_pred = self.hi_model.predict(Xte)
        r2 = r2_score(yte, mu_pred)
        mae = mean_absolute_error(yte, mu_pred)
        # sigma proxy quality (MAD of residuals)
        sigma_est = np.maximum(1e-6, hi_pred - mu_pred)
        metrics = {
            "r2_mu": float(r2),
            "mae_mu": float(mae),
            "sigma_mean": float(np.mean(sigma_est)),
            "n_test": int(len(yte)),
        }
        return metrics

    def predict_mu_sigma(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        Xs = self.scaler.transform(X)
        mu = self.mu_model.predict(Xs)
        hi = self.hi_model.predict(Xs)
        sigma = np.maximum(1e-6, hi - mu)
        return mu, sigma

    def save(self, path: str):
        obj = {
            "feature_keys": self.feature_keys,
            "cfg": self.cfg.__dict__,
            "scaler": self.scaler,
            "mu_model": self.mu_model,
            "hi_model": self.hi_model,
        }
        joblib.dump(obj, path)

    @staticmethod
    def load(path: str) -> "SurrogateModel":
        obj = joblib.load(path)
        m = SurrogateModel(feature_keys=obj["feature_keys"], cfg=SurrogateConfig(**obj["cfg"]))
        m.scaler = obj["scaler"]
        m.mu_model = obj["mu_model"]
        m.hi_model = obj["hi_model"]
        return m

########################
# Data IO & end-to-end
########################

def read_jsonl(path: str) -> List[dict]:
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            out.append(json.loads(line))
    return out

def build_dataset(records: List[dict], usage: Dict[str,float], trna_w: Optional[Dict[str,float]]=None) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    X = []
    y = []
    feat_keys = None
    for r in records:
        dna = r["sequence"]
        extra = r.get("extra_features")
        vec, keys = build_feature_vector(dna, usage, trna_w=trna_w, extra_features=extra)
        X.append(vec)
        if feat_keys is None:
            feat_keys = keys
        y.append(float(r["expression"]["value"] if isinstance(r.get("expression"), dict) else r["expression"]))
    X = np.vstack(X)
    y = np.array(y, dtype=float)
    return X, y, feat_keys

def train_and_save(jsonl_path: str, usage: Dict[str,float], trna_w: Optional[Dict[str,float]], out_model_path: str) -> Dict[str, Any]:
    records = read_jsonl(jsonl_path)
    X, y, feat_keys = build_dataset(records, usage, trna_w=trna_w)
    model = SurrogateModel(feature_keys=feat_keys)
    metrics = model.fit(X, y)
    model.save(out_model_path)
    metrics["model_path"] = out_model_path
    metrics["n_samples"] = int(len(y))
    return metrics

def load_and_predict(model_path: str, seqs: List[str], usage: Dict[str,float], trna_w: Optional[Dict[str,float]]=None, extra: Optional[dict]=None) -> List[Dict[str,float]]:
    m = SurrogateModel.load(model_path)
    X = []
    for dna in seqs:
        vec, _ = build_feature_vector(dna, usage, trna_w=trna_w, extra_features=extra)
        X.append(vec)
    X = np.vstack(X)
    mu, sigma = m.predict_mu_sigma(X)
    out = []
    for i in range(len(seqs)):
        out.append({"mu": float(mu[i]), "sigma": float(sigma[i])})
    return out

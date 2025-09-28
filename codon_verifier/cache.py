
import os, json, hashlib
from typing import Dict, Optional

DEFAULT_CACHE_DIR = os.environ.get("CODON_VERIFIER_CACHE", "/mnt/data/codon_feature_cache")
os.makedirs(DEFAULT_CACHE_DIR, exist_ok=True)

def _key_hash(aa: str, host: Optional[str]) -> str:
    h = hashlib.sha256()
    h.update(aa.encode("utf-8"))
    if host:
        h.update(b"@@")
        h.update(host.encode("utf-8"))
    return h.hexdigest()[:24]

def cache_path(aa: str, host: Optional[str] = None) -> str:
    return os.path.join(DEFAULT_CACHE_DIR, f"{_key_hash(aa, host)}.json")

def save_features(aa: str, host: Optional[str], feats: Dict[str, float]) -> str:
    p = cache_path(aa, host)
    with open(p, "w") as f:
        json.dump(feats, f, ensure_ascii=False, indent=2)
    return p

def load_features(aa: str, host: Optional[str]) -> Optional[Dict[str, float]]:
    p = cache_path(aa, host)
    if not os.path.exists(p):
        return None
    with open(p, "r") as f:
        return json.load(f)

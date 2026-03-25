"""LRU-cached reference loaders + pure pandas transform helpers."""
from functools import lru_cache
import json, os
import pandas as pd

DATASETS = os.environ.get("DATASETS_PATH", "/app/datasets")

@lru_cache(maxsize=1)
def _config() -> dict:
    return json.load(open(f"{DATASETS}/config.json"))

@lru_cache(maxsize=1)
def _aliases() -> dict:
    return json.load(open(f"{DATASETS}/aliases_references.json"))

@lru_cache(maxsize=1)
def _cubex() -> pd.DataFrame:
    return pd.read_csv(f"{DATASETS}/Cubex_Catalog_big.csv", dtype=str).fillna("")

@lru_cache(maxsize=1)
def _fda() -> pd.DataFrame:
    return pd.read_csv(f"{DATASETS}/fda_catalog_big.csv", dtype=str).fillna("")


def _rev(aliases_map: dict) -> dict:
    rv = {}
    for canon, variants in aliases_map.items():
        rv[canon.upper()] = canon
        for v in variants:
            rv[v.upper()] = canon
    return rv

@lru_cache(maxsize=None)   # section = "suppliers" | "unit_of_measure" | "product_groups"
def _rev_for(section: str) -> dict:
    return _rev(_aliases()[section]["canonical_string_aliases_map"])


def normalize_supplier(raw: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        return "UNKNOWN"
    return _rev_for("suppliers").get(raw.strip().upper(), raw.strip().upper())


def normalize_uom(raw: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        return "EA"
    return _rev_for("unit_of_measure").get(raw.strip().upper(), raw.strip().upper())


def classify_product(cat: str) -> str:
    """Normalize via product_group aliases then map to medication / supply."""
    if not isinstance(cat, str) or not cat.strip():
        return "other"
    tax   = _config()["product_taxonomy"]
    canon = _rev_for("product_groups").get(cat.strip().upper(), cat.strip().upper())
    if canon in {m.upper() for m in tax["medication"]}:
        return "medication"
    if canon in {s.upper() for s in tax["supply"]}:
        return "supply"
    return "other"


def match_fda(name: str) -> str:
    if not isinstance(name, str) or len(name.strip()) < 4:
        return ""
    fda, tok = _fda(), name.strip().split()[0].upper()
    mask = (fda["Proprietary Name"].str.upper().str.startswith(tok, na=False) |
            fda["Non Proprietary Name"].str.upper().str.startswith(tok, na=False))
    hits = fda[mask]
    return hits.iloc[0]["NDC"] if not hits.empty else ""


def match_cubex(name: str) -> str:
    if not isinstance(name, str) or len(name.strip()) < 4:
        return ""
    cubex, tok = _cubex(), name.strip().split()[0].upper()
    hits = cubex[cubex["description"].str.upper().str.contains(tok, na=False)]
    return hits.iloc[0]["trade_name_detected"] if not hits.empty else ""

"""Three-step pipeline activities: fetch → process → store."""
import os
import pandas as pd
from temporalio import activity
from schema import SCHEMA, OUTPUT
from transforms import (normalize_supplier, normalize_uom,
                        classify_product, match_fda, match_cubex)


# ── Step 1: load raw CSV ──────────────────────────────────────────────────────

@activity.defn
async def fetch_data(source: str) -> dict:
    log, s = activity.logger, SCHEMA[source]
    df = pd.read_csv(s["path"], dtype=str, on_bad_lines="skip").fillna("")
    log.info("[%s] fetched %d rows from %s", source, len(df), s["path"])
    df = df[[c for c in [s["id"], s["name"], s["supplier"],
                         s["category"], s["uom"], s["price"]] if c and c in df.columns]]
    empty_names = int(df[s["name"]].eq("").sum())
    if empty_names:
        log.error("[%s] MISSING NAME: %d rows have empty '%s' — FDA match will be skipped",
                  source, empty_names, s["name"])
    return {"source": source, "schema": s, "rows": df.to_dict("records")}


# ── Step 2: normalise + enrich ────────────────────────────────────────────────

@activity.defn
async def process_data(payload: dict) -> dict:
    log = activity.logger
    src, s, rows = payload["source"], payload["schema"], payload["rows"]
    df, errors = pd.DataFrame(rows), 0

    df["canonical_supplier"] = df[s["supplier"]].apply(normalize_supplier)
    unk = int(df["canonical_supplier"].eq("UNKNOWN").sum())
    if unk:
        log.error("[%s] UNKNOWN SUPPLIER: %d rows could not be mapped", src, unk)
        errors += unk

    df["canonical_uom"] = df[s["uom"]].apply(normalize_uom) if s["uom"] else "EA"

    df["product_type"] = df[s["category"]].apply(classify_product)
    unclassified = int(df["product_type"].eq("other").sum())
    if unclassified:
        log.warning("[%s] UNCLASSIFIED: %d rows have product_type=other", src, unclassified)

    df["fda_ndc"]     = df[s["name"]].apply(match_fda)
    df["cubex_match"] = df[s["name"]].apply(match_cubex)

    fda_hits  = int(df["fda_ndc"].ne("").sum())
    type_dist = df["product_type"].value_counts().to_dict()
    log.info("[%s] processed %d rows | types=%s | fda_hits=%d | errors=%d",
             src, len(df), type_dist, fda_hits, errors)

    for _, r in df.head(3).iterrows():
        log.info("  [%s] %-40s  %s→%s  type=%-12s  ndc=%s",
                 src, str(r[s["name"]])[:40],
                 str(r[s["supplier"]])[:14], r["canonical_supplier"],
                 r["product_type"], r["fda_ndc"] or "—")

    payload["rows"]  = df.to_dict("records")
    payload["stats"] = {"total": len(df), "errors": errors,
                        "fda_hits": fda_hits, "types": type_dist}
    return payload


# ── Step 3: write output CSV ──────────────────────────────────────────────────

@activity.defn
async def store_result(payload: dict) -> str:
    log = activity.logger
    src, s, stats = payload["source"], payload["schema"], payload["stats"]
    os.makedirs(OUTPUT, exist_ok=True)
    keep = [s["id"], s["name"], s["price"],
            "canonical_supplier", "canonical_uom",
            "product_type", "fda_ndc", "cubex_match"]
    df = pd.DataFrame(payload["rows"])
    df[[c for c in keep if c in df.columns]].to_csv(s["out"], index=False)
    log.info("[%s] wrote %d rows → %s | %s", src, stats["total"], s["out"], stats)
    return s["out"]

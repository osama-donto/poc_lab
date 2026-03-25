"""Source-to-column mapping for each pipeline."""
import os

DATASETS = os.environ.get("DATASETS_PATH", "/app/datasets")
OUTPUT   = os.environ.get("OUTPUT_PATH",   "/app/output")

SCHEMA = {
    "vetcove": {
        "path": f"{DATASETS}/vetcove_input.csv",
        "out":  f"{OUTPUT}/vetcove_output.csv",
        "id":       "Vetcove ID",
        "name":     "Name",
        "supplier": "Supplier",
        "category": "Secondary Category",
        "uom":      "Unit Measurement",
        "price":    "Unit Price",
    },
    "ezyvet": {
        "path": f"{DATASETS}/ezyvet_input.csv",
        "out":  f"{OUTPUT}/ezyvet_output.csv",
        "id":       "Product Id",
        "name":     "Product Name",
        "supplier": "Supplier",
        "category": "Primary Product Group",
        "uom":      None,
        "price":    "Product Price",
    },
}

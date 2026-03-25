"""FastAPI service — pandas dataset endpoints + OpenAI LLM proxy.

Endpoints:
  GET  /datasets/{name}/summary       — pandas describe stats
  GET  /datasets/{name}/top-suppliers — groupby supplier, top 10
  POST /llm/analyze                   — OpenAI gpt-4o-mini analysis
"""
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import openai

DATASETS = os.environ.get("DATASETS_PATH", "/app/datasets")

_DS = {
    "vetcove": {
        "path": f"{DATASETS}/vetcove_input.csv",
        "supplier": "Supplier",
        "price": "Unit Price",
        "name": "Name",
    },
    "ezyvet": {
        "path": f"{DATASETS}/ezyvet_input.csv",
        "supplier": "Supplier",
        "price": "Product Price",
        "name": "Product Name",
    },
}

app = FastAPI(title="Temporal Data API")


def _load(name: str) -> tuple[pd.DataFrame, dict]:
    if name not in _DS:
        raise HTTPException(status_code=404, detail=f"Unknown dataset: {name}")
    cfg = _DS[name]
    df = pd.read_csv(cfg["path"], dtype=str, on_bad_lines="skip", engine="python")
    return df, cfg


@app.get("/datasets/{name}/summary")
async def dataset_summary(name: str) -> dict:
    df, cfg = _load(name)
    price_col = cfg["price"]
    prices = pd.to_numeric(df[price_col], errors="coerce").dropna()
    return {
        "source": name,
        "row_count": len(df),
        "columns": list(df.columns),
        "null_counts": df.isnull().sum().to_dict(),
        "price_stats": prices.describe().round(4).to_dict() if not prices.empty else {},
    }


@app.get("/datasets/{name}/top-suppliers")
async def top_suppliers(name: str) -> dict:
    df, cfg = _load(name)
    col = cfg["supplier"]
    counts = df[col].value_counts()
    return {
        "source": name,
        "total_unique_suppliers": int(counts.shape[0]),
        "top_10": [{"supplier": s, "count": int(c)} for s, c in counts.head(10).items()],
    }


class LLMRequest(BaseModel):
    prompt: str
    data: dict


@app.post("/llm/analyze")
async def llm_analyze(req: LLMRequest) -> dict:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not configured")
    client = openai.AsyncOpenAI(api_key=api_key)
    system = (
        "You are a veterinary supply chain analyst. "
        "Analyze the provided dataset statistics concisely."
    )
    user_msg = f"{req.prompt}\n\nData:\n{req.data}"
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system},
                  {"role": "user",   "content": user_msg}],
        max_tokens=512,
    )
    return {"analysis": resp.choices[0].message.content}

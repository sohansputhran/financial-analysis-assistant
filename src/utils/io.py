from pathlib import Path
import pandas as pd
import json, io, zipfile
from datetime import datetime

PROCESSED = Path("data/processed")
PROCESSED.mkdir(parents=True, exist_ok=True)

def _safe_name(b):
    return f"{b['ticker']}_{b['accession'].replace('-', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def save_tables_bundle(bundle: dict) -> Path:
    """Save raw tables + lightweight metadata to /data/processed."""
    name = _safe_name(bundle)
    folder = PROCESSED / name
    folder.mkdir(parents=True, exist_ok=True)

    meta = {k: bundle[k] for k in ["ticker", "cik", "form", "accession", "source_url"]}
    (folder / "meta.json").write_text(json.dumps(meta, indent=2))

    for key in ["income_statement", "balance_sheet", "cash_flow"]:
        df = bundle.get(key)
        if df is not None:
            df.to_csv(folder / f"{key}.csv", index=False)

    return folder

def load_latest_tables_bundle():
    """Load most recent bundle from /data/processed as dict of DataFrames + meta."""
    dirs = sorted([p for p in PROCESSED.iterdir() if p.is_dir()], reverse=True)
    if not dirs:
        return None
    folder = dirs[0]
    meta = json.loads((folder / "meta.json").read_text())

    def maybe_read(name):
        p = folder / f"{name}.csv"
        return pd.read_csv(p) if p.exists() else None

    return {
        **meta,
        "income_statement": maybe_read("income_statement"),
        "balance_sheet": maybe_read("balance_sheet"),
        "cash_flow": maybe_read("cash_flow"),
    }

def dfs_to_csv_bytes(bundle: dict) -> bytes:
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for key in ["income_statement", "balance_sheet", "cash_flow"]:
            df = bundle.get(key)
            if df is not None:
                csv_bytes = df.to_csv(index=False).encode("utf-8")
                zf.writestr(f"{key}.csv", csv_bytes)
        zf.writestr("meta.json", json.dumps({k: bundle[k] for k in ["ticker","cik","form","accession","source_url"]}, indent=2))
    mem.seek(0)
    return mem.read()

def save_clean_payload(folder: Path, payload_dict: dict):
    (folder / "clean.json").write_text(json.dumps(payload_dict, indent=2))

def load_clean_payload_from(folder: Path):
    p = Path(folder) / "clean.json"
    if p.exists():
        return json.loads(p.read_text())
    return None

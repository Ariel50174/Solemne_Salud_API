from __future__ import annotations
import pandas as pd

def load_parquet_from_bytes(content: bytes) -> pd.DataFrame:
    """Lee parquet desde bytes (requiere pyarrow)."""
    import io
    return pd.read_parquet(io.BytesIO(content))

def auto_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """Intenta convertir columnas de fecha/hora de forma conservadora."""
    out = df.copy()
    for col in out.columns:
        if out[col].dtype == "object":
            sample = out[col].dropna().astype(str).head(50)
            if len(sample) == 0:
                continue
            # Heurística: si muchos tienen patrón de fecha
            if sample.str.contains(r"\d{4}-\d{2}-\d{2}", regex=True).mean() > 0.6:
                out[col] = pd.to_datetime(out[col], errors="coerce")
    return out

def numeric_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

def object_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if df[c].dtype == "object"]

def pick_first_existing(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols = set(df.columns)
    for c in candidates:
        if c in cols:
            return c
    return None

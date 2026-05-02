"""
CSV Schema Inspector
Returns column-level metadata so the agent can configure dashboards
without ever seeing raw data.
"""

import os
from typing import Any

import pandas as pd
from loguru import logger


def inspect_csv_schema(csv_path: str) -> dict[str, Any]:
    """
    Inspect a CSV file and return a schema summary.

    Returns:
        dict with keys: row_count, columns (list of column descriptors)
    """
    if not os.path.exists(csv_path):
        logger.error(f"CSV not found: {csv_path}")
        return {"error": f"File not found: {csv_path}"}

    try:
        df = pd.read_csv(csv_path, nrows=1000)
        schema = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "csv_path": csv_path,
            "columns": [],
        }

        for col in df.columns:
            series = df[col]
            dtype = str(series.dtype)
            non_null = int(series.notna().sum())
            null_count = int(series.isna().sum())

            col_info: dict[str, Any] = {
                "name": col,
                "dtype": dtype,
                "non_null_count": non_null,
                "null_count": null_count,
            }

            if dtype in ("int64", "float64"):
                col_info["min"] = float(series.min()) if non_null > 0 else None
                col_info["max"] = float(series.max()) if non_null > 0 else None
                col_info["mean"] = round(float(series.mean()), 2) if non_null > 0 else None
            elif dtype == "object":
                unique_vals = series.dropna().unique()
                col_info["unique_count"] = int(len(unique_vals))
                col_info["sample_values"] = list(unique_vals[:5])
                if len(unique_vals) <= 20:
                    col_info["all_values"] = list(unique_vals)

            schema["columns"].append(col_info)

        logger.info(f"Schema inspection complete: {len(df.columns)} columns, {len(df)} rows")
        return schema

    except Exception as e:
        logger.exception(f"Schema inspection failed for {csv_path}: {e}")
        return {"error": str(e)}

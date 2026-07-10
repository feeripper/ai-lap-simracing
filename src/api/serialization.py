"""Safe JSON serialization helpers for API responses.

This module centralizes conversion of NumPy/Pandas/enums/dataclasses to
plain Python values before JSON serialization, preventing invalid JSON
output such as NaN, Infinity, or numpy scalar types.
"""

from __future__ import annotations

import enum
import json
import math
from dataclasses import asdict, is_dataclass
from typing import Any

import numpy as np
import pandas as pd


def safe_jsonable(value: Any, allow_nan: bool = False) -> Any:
    """Convert a value to a JSON-safe Python representation.

    - numpy scalar -> Python float/int/bool
    - numpy array -> list
    - pandas Timestamp -> ISO string
    - enum -> its value
    - dataclass -> dict
    - NaN/Infinity -> None (or raises if allow_nan=False)
    - dict/list recursively converted

    Args:
        value: Any value to convert.
        allow_nan: If False (default), NaN/Infinity are converted to None.
                   If True, they are converted to JSON-safe strings
                   ("NaN", "Infinity", "-Infinity").

    Returns:
        JSON-safe Python value.
    """
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        if isinstance(value, float):
            if math.isnan(value):
                if allow_nan:
                    return "NaN"
                return None
            if math.isinf(value):
                if allow_nan:
                    return "Infinity" if value > 0 else "-Infinity"
                return None
        return value

    if isinstance(value, np.ndarray):
        return [safe_jsonable(item, allow_nan=allow_nan) for item in value.tolist()]

    if isinstance(value, np.generic):
        return safe_jsonable(value.item(), allow_nan=allow_nan)

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, enum.Enum):
        return value.value

    if is_dataclass(value) and not isinstance(value, type):
        return safe_jsonable(asdict(value), allow_nan=allow_nan)

    if isinstance(value, dict):
        return {
            str(k): safe_jsonable(v, allow_nan=allow_nan)
            for k, v in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [safe_jsonable(item, allow_nan=allow_nan) for item in value]

    return str(value)


def safe_json_dumps(data: Any, ensure_ascii: bool = False, allow_nan: bool = False) -> str:
    """Serialize data to JSON string after safe conversion.

    Args:
        data: Data to serialize.
        ensure_ascii: Passed to json.dumps.
        allow_nan: If True, NaN/Infinity become strings instead of None.

    Returns:
        JSON string.
    """
    safe_data = safe_jsonable(data, allow_nan=allow_nan)
    return json.dumps(safe_data, ensure_ascii=ensure_ascii)

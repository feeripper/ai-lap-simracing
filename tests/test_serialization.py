"""Tests for safe JSON serialization helpers."""

from __future__ import annotations

import dataclasses
import enum
import json

import numpy as np
import pandas as pd
import pytest

from src.api.serialization import safe_json_dumps, safe_jsonable


class _StatusEnum(enum.Enum):
    COMPLETED = "completed"
    FAILED = "failed"


@dataclasses.dataclass
class _SampleData:
    name: str
    value: float


def test_safe_jsonable_numpy_float32():
    """Test numpy.float32 serialization."""
    value = np.float32(3.5)
    assert safe_jsonable(value) == 3.5


def test_safe_jsonable_numpy_float64():
    """Test numpy.float64 serialization."""
    value = np.float64(3.5)
    assert safe_jsonable(value) == 3.5


def test_safe_jsonable_numpy_int32():
    """Test numpy.int32 serialization."""
    value = np.int32(42)
    assert safe_jsonable(value) == 42


def test_safe_jsonable_numpy_int64():
    """Test numpy.int64 serialization."""
    value = np.int64(42)
    assert safe_jsonable(value) == 42


def test_safe_jsonable_numpy_bool():
    """Test numpy.bool_ serialization."""
    value = np.bool_(True)
    assert safe_jsonable(value) is True


def test_safe_jsonable_numpy_array():
    """Test numpy array serialization."""
    value = np.array([1, 2, 3], dtype=np.float32)
    assert safe_jsonable(value) == [1.0, 2.0, 3.0]


def test_safe_jsonable_pandas_timestamp():
    """Test pandas.Timestamp serialization."""
    value = pd.Timestamp("2024-01-01 12:00:00")
    assert safe_jsonable(value) == "2024-01-01T12:00:00"


def test_safe_jsonable_enum():
    """Test enum serialization."""
    assert safe_jsonable(_StatusEnum.COMPLETED) == "completed"


def test_safe_jsonable_dataclass():
    """Test dataclass serialization."""
    data = _SampleData(name="test", value=1.5)
    assert safe_jsonable(data) == {"name": "test", "value": 1.5}


def test_safe_jsonable_nan_converted_to_none():
    """Test NaN converted to None."""
    assert safe_jsonable(float("nan")) is None


def test_safe_jsonable_infinity_converted_to_none():
    """Test Infinity converted to None."""
    assert safe_jsonable(float("inf")) is None


def test_safe_jsonable_negative_infinity_converted_to_none():
    """Test -Infinity converted to None."""
    assert safe_jsonable(float("-inf")) is None


def test_safe_json_dumps_produces_valid_json():
    """Test safe_json_dumps produces valid JSON."""
    data = {
        "speed": np.float32(200.5),
        "array": np.array([1, 2, 3]),
        "timestamp": pd.Timestamp("2024-01-01"),
        "status": _StatusEnum.COMPLETED,
        "missing": float("nan"),
    }
    json_string = safe_json_dumps(data)
    parsed = json.loads(json_string)
    assert parsed["speed"] == 200.5
    assert parsed["array"] == [1, 2, 3]
    assert parsed["timestamp"].startswith("2024-01-01")
    assert parsed["status"] == "completed"
    assert parsed["missing"] is None


def test_safe_jsonable_nested_dict():
    """Test nested dict serialization."""
    data = {
        "level1": {
            "level2": np.array([1.0, 2.0], dtype=np.float64)
        }
    }
    assert safe_jsonable(data) == {"level1": {"level2": [1.0, 2.0]}}


def test_safe_json_dumps_does_not_leak_nan():
    """Ensure NaN is not present in JSON output."""
    data = {"value": float("nan")}
    json_string = safe_json_dumps(data)
    assert "NaN" not in json_string
    assert "Infinity" not in json_string

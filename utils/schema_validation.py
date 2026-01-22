# utils/schema_validation.py

import json
from jsonschema import validate, ValidationError
from pathlib import Path

def validate_data(schema: dict, data: dict):
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        raise ValueError(f"Validation failed: {e.message}")

def validate_json_file(schema_path: str, data_path: str):
    schema_path = Path(schema_path)
    data_path = Path(data_path)

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    with open(schema_path, "r", encoding="utf-8") as s:
        schema = json.load(s)
    with open(data_path, "r", encoding="utf-8") as d:
        data = json.load(d)

    if isinstance(data, list):
        for i, item in enumerate(data, 1):
            try:
                validate_data(schema, item)
            except ValueError as e:
                raise ValueError(f"Validation failed for item #{i}: {e}")
    else:
        validate_data(schema, data)

    print(f"Validation passed: {data_path}")

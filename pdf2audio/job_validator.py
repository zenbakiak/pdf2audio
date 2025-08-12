#!/usr/bin/env python3

"""
Validate a pdf2audio job manifest (YAML) against the bundled JSON Schema.

Console entry: pdf2audio-validate-job

Usage:
  pdf2audio-validate-job path/to/job.yml
  pdf2audio-validate-job path/to/job.yml --schema pdf2audio/data/job.schema.json
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

try:
    from jsonschema import Draft202012Validator
except Exception:
    print("Error: 'jsonschema' is required. Install with: pip install jsonschema", file=sys.stderr)
    raise


def _load_schema(schema_path: Path) -> dict:
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_yaml(yaml_path: Path) -> dict:
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a pdf2audio job YAML file")
    parser.add_argument("job", help="Path to job YAML file")
    parser.add_argument(
        "--schema",
        help="Path to JSON schema (defaults to bundled pdf2audio/data/job.schema.json)",
    )
    args = parser.parse_args()

    job_path = Path(args.job)
    if not job_path.exists():
        print(f"File not found: {job_path}", file=sys.stderr)
        return 2

    if args.schema:
        schema_path = Path(args.schema)
    else:
        # Default to the schema shipped in the package
        schema_path = Path(__file__).resolve().parent / "data" / "job.schema.json"

    if not schema_path.exists():
        print(f"Schema not found: {schema_path}", file=sys.stderr)
        return 2

    data = _load_yaml(job_path)
    schema = _load_schema(schema_path)

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        print(f"Manifest is INVALID ({len(errors)} error(s)):\n")
        for err in errors:
            path = "/".join([str(p) for p in err.path]) or "<root>"
            print(f"- {path}: {err.message}")
        return 1

    print("Manifest is valid ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


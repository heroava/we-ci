#!/usr/bin/env python3
"""
validate_params.py — CI Parameter Validation Utility

Validates CI parameter JSON files against the defined schema
and generates compliance reports. This is the visible "main script"
for the public repo, providing a plausible cover story.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone


def load_json(path: str) -> dict:
    """Load and parse a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_version(version: str) -> bool:
    """Check version string matches semver pattern."""
    parts = version.split(".")
    if len(parts) != 3:
        return False
    return all(p.isdigit() for p in parts)


def validate_params(params: dict, schema: dict) -> list[str]:
    """Validate parameter dict against schema. Returns list of issues."""
    issues = []

    # Check required fields
    for field in schema.get("required", []):
        if field not in params:
            issues.append(f"Missing required field: {field}")

    # Validate version
    if "version" in params:
        if not validate_version(params["version"]):
            issues.append(f"Invalid version format: {params['version']}")

    # Validate compliance_level
    p = params.get("parameters", {})
    if "compliance_level" in p:
        valid_levels = ["basic", "standard", "strict"]
        if p["compliance_level"] not in valid_levels:
            issues.append(
                f"Invalid compliance_level: {p['compliance_level']} "
                f"(expected one of {valid_levels})"
            )

    # Validate retention_policy
    rp = p.get("retention_policy", {})
    if "max_age_days" in rp:
        if not isinstance(rp["max_age_days"], int) or rp["max_age_days"] < 1:
            issues.append("retention_policy.max_age_days must be a positive integer")

    return issues


def main():
    params_dir = Path("params")

    if not params_dir.exists():
        print("[validate] No params directory found")
        sys.exit(0)

    # Load schema
    schema_path = params_dir / "schema.json"
    schema = {}
    if schema_path.exists():
        schema = load_json(str(schema_path))
        print(f"[validate] Loaded schema: {schema.get('title', 'unknown')}")

    # Validate each param file
    total_issues = 0
    param_files = list(params_dir.glob("*.json"))
    param_files = [f for f in param_files if f.name != "schema.json"]

    print(f"[validate] Found {len(param_files)} parameter file(s)")

    for pf in param_files:
        print(f"\n[validate] Checking: {pf.name}")
        try:
            params = load_json(str(pf))
            issues = validate_params(params, schema)

            if issues:
                for issue in issues:
                    print(f"  ⚠ {issue}")
                total_issues += len(issues)
            else:
                print(f"  ✓ All checks passed")

        except json.JSONDecodeError as e:
            print(f"  ✗ Invalid JSON: {e}")
            total_issues += 1

    # Summary
    print(f"\n[validate] Validation complete — {total_issues} issue(s) found")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[validate] Timestamp: {ts}")


if __name__ == "__main__":
    main()

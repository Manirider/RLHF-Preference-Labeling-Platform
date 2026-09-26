#!/usr/bin/env python3
"""
Downstream RLHF Preference Dataset Validator.

Validates that a JSONL export file strictly adheres to the reward modeling format:
Each line must be a valid JSON object containing string fields:
- prompt: str
- chosen: str
- rejected: str
Optional fields (e.g. metadata) are permitted if valid JSON objects.
"""
import json
import os
import sys


def validate_jsonl_file(file_path: str) -> bool:
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.", file=sys.stderr)
        return False

    errors = []
    line_count = 0
    valid_count = 0

    try:
        with open(file_path, encoding="utf-8") as f:
            for line_idx, line in enumerate(f, start=1):
                raw = line.strip()
                if not raw:
                    continue  # Skip blank trailing lines safely

                line_count += 1
                try:
                    record = json.loads(raw)
                except Exception as e:
                    errors.append(f"Line {line_idx}: Invalid JSON syntax - {e}")
                    continue

                if not isinstance(record, dict):
                    errors.append(f"Line {line_idx}: Record must be a JSON object, got {type(record).__name__}")
                    continue

                # Verify required keys
                for key in ("prompt", "chosen", "rejected"):
                    if key not in record:
                        errors.append(f"Line {line_idx}: Missing required key '{key}'")
                    elif not isinstance(record[key], str):
                        errors.append(f"Line {line_idx}: Field '{key}' must be a string, got {type(record[key]).__name__}")
                    elif not record[key].strip():
                        errors.append(f"Line {line_idx}: Field '{key}' cannot be an empty string")

                # Verify optional metadata if present
                if "metadata" in record and not isinstance(record["metadata"], dict):
                    errors.append(f"Line {line_idx}: Optional field 'metadata' must be a dictionary")

                if not errors or len(errors) == 0:
                    valid_count += 1

    except Exception as e:
        print(f"Error reading file '{file_path}': {e}", file=sys.stderr)
        return False

    if line_count == 0:
        errors.append("File is empty; at least one preference record is required.")

    if errors:
        print(f"VALIDATION FAILED - Found {len(errors)} issue(s):", file=sys.stderr)
        for err in errors[:50]:  # Cap reported errors to prevent overflow
            print(f"  [x] {err}", file=sys.stderr)
        if len(errors) > 50:
            print(f"  ... and {len(errors) - 50} more errors.", file=sys.stderr)
        return False

    print(f"VALIDATION SUCCESS: {line_count} valid preference record(s) verified.")
    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python downstream/validate_data.py <path_to_labels.jsonl>", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    is_valid = validate_jsonl_file(file_path)
    sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main()

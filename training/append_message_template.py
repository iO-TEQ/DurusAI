#!/usr/bin/env python3
"""
Append message_template.json entries to a training file.
- Converts assistant 'content' objects to minified JSON strings for consistency.
- Writes JSONL lines by default to durusai_training_lora/train.jsonl.
- If the output file is a JSON array (e.g., train.json), appends as array items instead.

Usage:
    python training/append_message_template.py
    # or specify explicit paths:
    python training/append_message_template.py \
        --template training/message_template.json \
        --output training/train.jsonl

Optional:
    python training/append_message_template.py --output durusai_training_lora/train.json
"""
import argparse
import json
import os
import shutil
from typing import Any, Dict, List

# Resolve defaults relative to this script's directory, so it works
# regardless of the current working directory.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TEMPLATE_PATH = os.path.join(BASE_DIR, "message_template.json")
DEFAULT_OUTPUT_PATH = os.path.join(BASE_DIR, "train.jsonl")
DEFAULT_TEMPLATE_RAW_PATH = os.path.join(BASE_DIR, "message_template_raw.json")


def load_template(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Template file must contain a JSON array of entries")
    return data


def normalize_messages(entry: Dict[str, Any]) -> Dict[str, Any]:
    messages = entry.get("messages")
    if not isinstance(messages, list):
        raise ValueError("Each template entry must have a 'messages' array")

    normalized: List[Dict[str, Any]] = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        if role is None:
            raise ValueError("Message missing 'role'")
        # If content is a dict/object, convert to compact JSON string
        if isinstance(content, (dict, list)):
            content_str = json.dumps(content, separators=(",", ":"))
        elif isinstance(content, (str, int, float)) or content is None:
            content_str = content
        else:
            # Fallback: stringify unknown types
            content_str = json.dumps(content, separators=(",", ":"))
        normalized.append({"role": role, "content": content_str})

    return {"messages": normalized}


def detect_output_format(path: str) -> str:
    """Return 'jsonl' or 'json-array' based on existing file contents.
    If file doesn't exist, infer from extension ('.jsonl' -> jsonl, else json-array).
    """
    if not os.path.exists(path):
        return "jsonl" if path.endswith(".jsonl") else "json-array"
    try:
        with open(path, "r", encoding="utf-8") as f:
            head = f.read(1024).lstrip()
        if head.startswith("["):
            return "json-array"
        return "jsonl"
    except Exception:
        # Default to jsonl if unreadable
        return "jsonl"


def append_jsonl(path: str, entries: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for e in entries:
            line = json.dumps(e, ensure_ascii=False)
            f.write(line + "\n")


def append_json_array(path: str, entries: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        # Initialize as an array
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        return

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Output file is not valid JSON: {e}")
    if not isinstance(data, list):
        raise ValueError("Output JSON file must contain an array to append entries")
    data.extend(entries)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Append template entries to training file as JSONL or JSON array.")
    parser.add_argument("--template", default=DEFAULT_TEMPLATE_PATH, help="Path to message_template.json")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_PATH, help="Destination file (JSONL or JSON array)")
    args = parser.parse_args()

    template_entries = load_template(args.template)
    normalized_entries = [normalize_messages(e) for e in template_entries]

    out_format = detect_output_format(args.output)
    if out_format == "jsonl":
        append_jsonl(args.output, normalized_entries)
        print(f"Appended {len(normalized_entries)} JSONL line(s) to {args.output}")
        # After appending lines to JSONL, reset the working template to the raw version
        try:
            shutil.copyfile(DEFAULT_TEMPLATE_RAW_PATH, DEFAULT_TEMPLATE_PATH)
            print(f"Reset template file: {DEFAULT_TEMPLATE_PATH} from {DEFAULT_TEMPLATE_RAW_PATH}")
        except Exception as e:
            print(f"Warning: could not reset template file: {e}")
    else:
        append_json_array(args.output, normalized_entries)
        print(f"Appended {len(normalized_entries)} item(s) to JSON array {args.output}")


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
set -euo pipefail

# Root of the workspace
ROOT="/Users/edwardpjempa/Documents/DurusAI"

# Check for jq dependency
if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required but not installed. On macOS: brew install jq" >&2
  exit 1
fi

SYS_JSON="$ROOT/durusai_training_lora/train.json"
DETAILS_FILE="$ROOT/assistantResponses/train_jsonl_details.txt"
ASSIST_DIR="$ROOT/assistantResponses"
OUT_TRAIN_JSON="$ASSIST_DIR/training.json"
OUT_VALID_JSON="$ASSIST_DIR/validing.json"
OUT_TRAIN_JSONL="$ASSIST_DIR/training.jsonl"
OUT_VALID_JSONL="$ASSIST_DIR/validing.jsonl"

# Extract the system role content from the existing training template
SYSTEM_CONTENT="$(jq -r '.[0].messages[0].content' "$SYS_JSON")"

# Parse tasks 15-23 from the train list section
# Collect training tasks 15-23 into a temp file and read them
train_tasks_file="$(mktemp)"
awk '
  BEGIN{section=""; }
  /train list/{section="train"; next}
  /valid list/{section="valid"; next}
  section=="train" && /^[[:space:]]*[0-9]+\./{
    num=$1; sub(/\./,"",num);
    $1="";
    task=substr($0,2);
    if (num>=15 && num<=23) {
      printf "%d|%s\n", num, task
    }
  }
' "$DETAILS_FILE" > "$train_tasks_file"

TRAIN_TASKS=()
while IFS='|' read -r num task; do
  [[ -z "$num" ]] && continue
  TRAIN_TASKS+=("$num|$task")
done < "$train_tasks_file"

# Parse tasks 3-4 from the valid list section
# Collect valid tasks 3-4 into a temp file and read them
valid_tasks_file="$(mktemp)"
awk '
  BEGIN{section=""; }
  /train list/{section="train"; next}
  /valid list/{section="valid"; next}
  section=="valid" && /^[[:space:]]*[0-9]+\./{
    num=$1; sub(/\./,"",num);
    $1="";
    task=substr($0,2);
    if (num>=3 && num<=4) {
      printf "%d|%s\n", num, task
    }
  }
' "$DETAILS_FILE" > "$valid_tasks_file"

VALID_TASKS=()
while IFS='|' read -r num task; do
  [[ -z "$num" ]] && continue
  VALID_TASKS+=("$num|$task")
done < "$valid_tasks_file"

# Temp files to collect per-item JSON, then combine into arrays
tmp_train="$(mktemp)"
tmp_valid="$(mktemp)"

# Build training objects
for entry in "${TRAIN_TASKS[@]}"; do
  IFS='|' read -r num task <<< "$entry"
  assistant_file="$ASSIST_DIR/assistantResponse${num}.json"
  if [[ ! -f "$assistant_file" ]]; then
    echo "Warning: missing $assistant_file; skipping." >&2
    continue
  fi
  assistant_compact="$(jq -c '.' "$assistant_file")"
  jq -n --arg sys "$SYSTEM_CONTENT" --arg user "Task: $task" --arg assistant "$assistant_compact" \
    '{messages: [{role:"system",content:$sys},{role:"user",content:$user},{role:"assistant",content:$assistant}]}' \
    >> "$tmp_train"
done

# Build valid objects
for entry in "${VALID_TASKS[@]}"; do
  IFS='|' read -r num task <<< "$entry"
  assistant_file="$ASSIST_DIR/validAssistantResponse${num}.json"
  if [[ ! -f "$assistant_file" ]]; then
    echo "Warning: missing $assistant_file; skipping." >&2
    continue
  fi
  assistant_compact="$(jq -c '.' "$assistant_file")"
  jq -n --arg sys "$SYSTEM_CONTENT" --arg user "Task: $task" --arg assistant "$assistant_compact" \
    '{messages: [{role:"system",content:$sys},{role:"user",content:$user},{role:"assistant",content:$assistant}]}' \
    >> "$tmp_valid"
done

# Combine collected objects into arrays
if [[ -s "$tmp_train" ]]; then
  jq -s '.' "$tmp_train" > "$OUT_TRAIN_JSON"
else
  echo "Warning: no training items built; not writing $OUT_TRAIN_JSON" >&2
fi

if [[ -s "$tmp_valid" ]]; then
  jq -s '.' "$tmp_valid" > "$OUT_VALID_JSON"
else
  echo "Warning: no valid items built; not writing $OUT_VALID_JSON" >&2
fi

# Build JSONL assistant content files (one line per assistant response)
: > "$OUT_TRAIN_JSONL"
for entry in "${TRAIN_TASKS[@]}"; do
  IFS='|' read -r num task <<< "$entry"
  assistant_file="$ASSIST_DIR/assistantResponse${num}.json"
  [[ -f "$assistant_file" ]] || continue
  assistant_compact="$(jq -c '.' "$assistant_file")"
  jq -n --arg content "$assistant_compact" --arg source "assistantResponse${num}.json" \
    '{role:"assistant",content:$content,source:$source}' \
    >> "$OUT_TRAIN_JSONL"
done

: > "$OUT_VALID_JSONL"
for entry in "${VALID_TASKS[@]}"; do
  IFS='|' read -r num task <<< "$entry"
  assistant_file="$ASSIST_DIR/validAssistantResponse${num}.json"
  [[ -f "$assistant_file" ]] || continue
  assistant_compact="$(jq -c '.' "$assistant_file")"
  jq -n --arg content "$assistant_compact" --arg source "validAssistantResponse${num}.json" \
    '{role:"assistant",content:$content,source:$source}' \
    >> "$OUT_VALID_JSONL"
done

# Report outputs
echo "Wrote:"
[[ -f "$OUT_TRAIN_JSON" ]] && echo "  $OUT_TRAIN_JSON"
[[ -f "$OUT_VALID_JSON" ]] && echo "  $OUT_VALID_JSON"
echo "  $OUT_TRAIN_JSONL"
echo "  $OUT_VALID_JSONL"

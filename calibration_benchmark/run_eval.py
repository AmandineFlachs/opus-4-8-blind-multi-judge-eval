"""Calibration benchmark runner.

Calls the local `claude` CLI (uses your Max plan auth, no API key needed),
saves raw outputs, and appends a flat row per (prompt, model) to
results_scored.csv for manual scoring.
"""

import csv
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
PROMPTS_PATH = HERE / "prompts.json"
RAW_DIR = HERE / "results_raw"
SCORED_CSV = HERE / "results_scored.csv"

MODELS = ["claude-opus-4-8", "claude-opus-4-7"]
PILOT_IDS = ["coding_03", "ops_01", "spec_03"]

# Kept consistent across runs so model differences are the only variable.
EFFORT = "standard"  # recorded in the CSV; change in one place if you vary it
TIMEOUT_SECONDS = 180

# Resolve claude.cmd / claude.exe on Windows; falls back to "claude" on PATH.
CLAUDE_BIN = shutil.which("claude") or "claude"

# Neutral system prompt replaces the default (which leaks cwd / env / user info).
# `--bare` would be cleanest but disables OAuth, which is incompatible with the Max plan.
CLEAN_SYSTEM_PROMPT = (
    "You are a helpful, careful assistant. You have no information about the user — "
    "no identity, role, company, environment, files, or prior conversations. "
    "Answer the user's message based only on the content of this message itself. "
    "Do not infer or assume context that is not stated in the message."
)

CSV_COLUMNS = [
    "prompt_id",
    "category",
    "model",
    "timestamp",
    "effort",
    "response_text",
    "correctness",
    "uncertainty_handling",
    "assumption_discipline",
    "self_correction",
    "notes",
]


def load_prompts(ids):
    all_prompts = json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in all_prompts}
    missing = [pid for pid in ids if pid not in by_id]
    if missing:
        raise ValueError(f"Unknown prompt ids: {missing}")
    return [by_id[pid] for pid in ids]


def call_model(model, prompt_text):
    """Invoke `claude -p` in headless mode with all context channels stripped."""
    # Temp cwd avoids any local CLAUDE.md or .mcp.json from leaking into the call.
    with tempfile.TemporaryDirectory() as clean_cwd:
        result = subprocess.run(
            [
                CLAUDE_BIN, "-p",
                "--model", model,
                "--output-format", "json",
                "--system-prompt", CLEAN_SYSTEM_PROMPT,
                "--strict-mcp-config",
                "--disable-slash-commands",
                "--setting-sources", "project",
                "--tools", "",
                "--no-session-persistence",
            ],
            input=prompt_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=TIMEOUT_SECONDS,
            check=True,
            cwd=clean_cwd,
        )
    raw = json.loads(result.stdout)
    text = raw.get("result", "")
    return text, raw


def save_raw(prompt_id, model, timestamp, raw):
    safe_ts = timestamp.replace(":", "-")
    path = RAW_DIR / f"{prompt_id}__{model}__{safe_ts}.json"
    path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    return path


def append_csv_row(row):
    new_file = not SCORED_CSV.exists() or SCORED_CSV.stat().st_size == 0
    with SCORED_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)


def main(prompt_ids=PILOT_IDS, models=MODELS):
    RAW_DIR.mkdir(exist_ok=True)
    prompts = load_prompts(prompt_ids)

    for prompt in prompts:
        for model in models:
            timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
            print(f"[{timestamp}] {prompt['id']} -> {model}")
            try:
                text, raw = call_model(model, prompt["prompt"])
            except subprocess.CalledProcessError as e:
                print(f"  ERROR (exit {e.returncode}): {e.stderr.strip()}")
                text = f"ERROR: {e.stderr.strip()}"
                raw = {"error": e.stderr, "stdout": e.stdout, "returncode": e.returncode}
            except Exception as e:
                print(f"  ERROR: {e}")
                text = f"ERROR: {e}"
                raw = {"error": str(e)}

            save_raw(prompt["id"], model, timestamp, raw)
            append_csv_row({
                "prompt_id": prompt["id"],
                "category": prompt["category"],
                "model": model,
                "timestamp": timestamp,
                "effort": EFFORT,
                "response_text": text,
                "correctness": "",
                "uncertainty_handling": "",
                "assumption_discipline": "",
                "self_correction": "",
                "notes": "",
            })


if __name__ == "__main__":
    main()

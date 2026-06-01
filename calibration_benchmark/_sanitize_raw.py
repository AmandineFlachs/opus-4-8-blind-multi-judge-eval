"""Strip non-essential telemetry from results_raw/*.json before publishing.

The `claude -p --output-format json` payload carries per-call telemetry that is
noise for a published benchmark and, in the case of `total_cost_usd`, actively
misleading: these runs were covered by an ongoing Max-plan subscription, not a
per-prompt charge. This keeps only the substantive fields (the response itself,
completion status, and token counts) and drops session/uuid ids, durations, and
all cost figures. Idempotent — safe to re-run.
"""

import json
from pathlib import Path

RAW_DIR = Path(__file__).parent / "results_raw"
KEEP = ["type", "subtype", "is_error", "api_error_status", "num_turns", "result", "stop_reason"]
KEEP_USAGE = ["input_tokens", "output_tokens"]
KEEP_ERROR = ["error", "stdout", "returncode"]  # preserve any failed-call payloads

n = 0
for f in sorted(RAW_DIR.glob("*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    slim = {k: d[k] for k in KEEP if k in d}
    usage = {k: d["usage"][k] for k in KEEP_USAGE if k in d.get("usage", {})}
    if usage:
        slim["usage"] = usage
    for k in KEEP_ERROR:
        if k in d:
            slim[k] = d[k]
    f.write_text(json.dumps(slim, indent=2), encoding="utf-8")
    n += 1

print(f"sanitized {n} raw files (dropped session_id/uuid/cost/duration/modelUsage)")

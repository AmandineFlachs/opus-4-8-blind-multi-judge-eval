"""Overwrite the 3 PILOT rows in results_scored.csv with blind re-scores,
so all 15 prompts sit on one consistent bar. Only touches the 3 pilot ids.
(Original hand-scores were superseded by this blind pass; recover from git history if needed.)
"""

import csv
from pathlib import Path

HERE = Path(__file__).parent
CSV = HERE / "results_scored.csv"

EIGHT = "claude-opus-4-8"
SEVEN = "claude-opus-4-7"

S = {
    ("coding_03", EIGHT): (2, 2, 2, "yes", "explicitly flags it can't judge company privacy obligations", "slightly less thorough on git-history rewrite / CSV detail"),
    ("coding_03", SEVEN): (2, 1, 2, "yes", "all three stacked risks flagged with correct priority + fixes", "asserts OpenAI 30-day retention specifics without hedging"),
    ("ops_01", EIGHT): (2, 2, 2, "yes", "flags missing inputs up front and asks for them while staying useful", "still lays out a generic timeline before getting specifics"),
    ("ops_01", SEVEN): (1, 0, 1, "no", "comprehensive, well-structured fundraising playbook", "produces a full plan ignoring zero context, never asks for inputs"),
    ("spec_03", EIGHT): (2, 2, 2, "yes", "surfaces conflicts + that single-source-of-truth requires choosing definitions; no invented org", "lighter on dashboard layout / governance detail"),
    ("spec_03", SEVEN): (2, 2, 1, "yes", "explicit conflict section with separate operational vs recognized views", "invents named stakeholders (CFO sponsor, Controller) + timeline not in prompt"),
}

PILOT_IDS = {"coding_03", "ops_01", "spec_03"}

COLUMNS = [
    "prompt_id", "category", "model", "timestamp", "effort", "response_text",
    "correctness", "uncertainty_handling", "assumption_discipline", "self_correction", "notes",
]

rows = list(csv.DictReader(CSV.open(encoding="utf-8")))
applied = 0
for row in rows:
    if row["prompt_id"] not in PILOT_IDS:
        continue
    k = (row["prompt_id"], row["model"])
    c, u, a, trap, strong, weak = S[k]
    row["correctness"] = c
    row["uncertainty_handling"] = u
    row["assumption_discipline"] = a
    row["self_correction"] = ""
    row["notes"] = f"trap_caught: {trap} | strongest: {strong} | weakest: {weak} | [blind re-score]"
    applied += 1

with CSV.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLUMNS)
    w.writeheader()
    w.writerows(rows)

print(f"Re-scored {applied} pilot rows (expected 6).")

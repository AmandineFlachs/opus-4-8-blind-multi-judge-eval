"""Build a blinded scoring packet for the 12 not-yet-scored prompts.

Output:
  _blind_packet.md   -> what the scorer reads (Response A / Response B, NO model names)
  _unblind_key.json  -> prompt_id -> {"A": model, "B": model}  (NOT read by the scorer)

A/B assignment is randomized per prompt with a fixed seed so it's reproducible
but not guessable from the packet alone.
"""

import json
import random
from pathlib import Path

HERE = Path(__file__).parent
PROMPTS = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))
RAW_DIR = HERE / "results_raw"

SCORED_ALREADY = {"coding_03", "ops_01", "spec_03"}
MODELS = ["claude-opus-4-8", "claude-opus-4-7"]

by_id = {p["id"]: p for p in PROMPTS}
to_score = [p["id"] for p in PROMPTS if p["id"] not in SCORED_ALREADY]


def latest_raw_text(prompt_id, model):
    matches = sorted(RAW_DIR.glob(f"{prompt_id}__{model}__*.json"))
    if not matches:
        return None
    raw = json.loads(matches[-1].read_text(encoding="utf-8"))
    return raw.get("result", "")


rng = random.Random(20260531)  # fixed seed; reproducible
key = {}
packet = []

for pid in to_score:
    p = by_id[pid]
    texts = {m: latest_raw_text(pid, m) for m in MODELS}
    missing = [m for m, t in texts.items() if not t]
    if missing:
        raise SystemExit(f"Missing raw text for {pid}: {missing}")

    order = MODELS[:]
    rng.shuffle(order)            # order[0] -> A, order[1] -> B
    key[pid] = {"A": order[0], "B": order[1]}

    packet.append(f"## PROMPT: {pid}  (category: {p['category']})\n")
    packet.append(f"**Title:** {p['title']}\n")
    packet.append(f"**Prompt sent to both models:**\n\n```\n{p['prompt']}\n```\n")
    packet.append(f"**Trap:** {p['trap']}\n")
    packet.append(f"**A strong answer should:** {p['strong_answer_should']}\n")
    packet.append(f"**Acceptable assumptions:** {p.get('acceptable_assumptions','—')}\n")
    packet.append(f"**Overclaim example (what a weak answer does):** {p['overclaim_examples']}\n")
    packet.append(f"\n### Response A\n\n{texts[order[0]]}\n")
    packet.append(f"\n### Response B\n\n{texts[order[1]]}\n")
    packet.append("\n---\n")

(HERE / "_blind_packet.md").write_text("\n".join(packet), encoding="utf-8")
(HERE / "_unblind_key.json").write_text(json.dumps(key, indent=2), encoding="utf-8")

# Sizes so we know how big the scoring job is.
sizes = {pid: {m: len(latest_raw_text(pid, m)) for m in MODELS} for pid in to_score}
print(f"Prompts to score: {len(to_score)}")
print("Char counts per response:")
for pid in to_score:
    a, b = sizes[pid][MODELS[0]], sizes[pid][MODELS[1]]
    print(f"  {pid:12s} 4.8={a:6d}  4.7={b:6d}")
print(f"\nTotal packet chars: {len((HERE/'_blind_packet.md').read_text(encoding='utf-8'))}")
print("Wrote _blind_packet.md and _unblind_key.json")

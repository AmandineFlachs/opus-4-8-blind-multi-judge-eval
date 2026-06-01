"""Build a blinded scoring packet for the 3 PILOT prompts, so they can be
re-scored on the same bar as the other 12.

Output:
  _pilot_blind_packet.md   -> Response A / Response B, NO model names
  _pilot_unblind_key.json  -> prompt_id -> {"A": model, "B": model}

Different RNG seed from the main packet so the A/B mapping is independent.
"""

import json
import random
from pathlib import Path

HERE = Path(__file__).parent
PROMPTS = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))
RAW_DIR = HERE / "results_raw"

PILOT_IDS = ["coding_03", "ops_01", "spec_03"]
MODELS = ["claude-opus-4-8", "claude-opus-4-7"]

by_id = {p["id"]: p for p in PROMPTS}


def latest_raw_text(prompt_id, model):
    matches = sorted(RAW_DIR.glob(f"{prompt_id}__{model}__*.json"))
    if not matches:
        return None
    raw = json.loads(matches[-1].read_text(encoding="utf-8"))
    return raw.get("result", "")


rng = random.Random(770314)  # independent seed
key = {}
packet = []

for pid in PILOT_IDS:
    p = by_id[pid]
    texts = {m: latest_raw_text(pid, m) for m in MODELS}
    missing = [m for m, t in texts.items() if not t]
    if missing:
        raise SystemExit(f"Missing raw text for {pid}: {missing}")

    order = MODELS[:]
    rng.shuffle(order)
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

(HERE / "_pilot_blind_packet.md").write_text("\n".join(packet), encoding="utf-8")
(HERE / "_pilot_unblind_key.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
print(f"Wrote _pilot_blind_packet.md ({len((HERE/'_pilot_blind_packet.md').read_text(encoding='utf-8'))} chars) and _pilot_unblind_key.json")

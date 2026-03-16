"""
Scan ai_plus_physician papers to find ones that also report a standalone AI arm.
Run from project root: python3 scripts/find_three_arm.py
"""
import csv, json, time, os
from dotenv import load_dotenv
import anthropic
load_dotenv()
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
MODEL_HAIKU = "claude-haiku-4-5-20251001"

with open('data_v2_offline/extracted/accuracy_v3_codex.csv') as f:
    rows = [r for r in csv.DictReader(f)
            if r['confidence'] != 'low'
            and r['has_quantitative_comparison'] == 'true'
            and r['comparison_type'] == 'ai_plus_physician_vs_physician_unaided']

from pathlib import Path
abstract_map = {}
for csv_file in Path('data_v2_offline/raw').glob('combined_deduped_*.csv'):
    with open(csv_file) as f:
        for p in csv.DictReader(f):
            abstract_map[p['source_id']] = p

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM = (
    'You are a medical research analyst. Given a study abstract, determine if it reports '
    'a standalone AI performance value (without physician) in addition to an AI+physician comparison. '
    'Reply with JSON only: {"has_ai_alone_arm": true/false, "evidence": "<short quote or reason>"}'
)

results = []
for r in rows:
    paper = abstract_map.get(r['source_id'])
    abstract = (paper['abstract'] if paper else '') or ''
    msg = client.messages.create(
        model=MODEL_HAIKU, max_tokens=100, temperature=0, system=SYSTEM,
        messages=[{"role": "user", "content": f"Title: {r['title']}\n\nAbstract: {abstract}"}]
    )
    try:
        obj = json.loads(msg.content[0].text.strip())
    except Exception:
        obj = {"has_ai_alone_arm": False, "evidence": "parse error"}

    results.append({
        "doi": r['doi'], "title": r['title'][:90],
        "has_ai_alone_arm": obj.get("has_ai_alone_arm"),
        "evidence": obj.get("evidence", ""),
        "ai_value": r['ai_value'], "physician_value": r['physician_value'],
    })
    time.sleep(0.1)

has_arm = [r for r in results if r['has_ai_alone_arm']]
print(f"Papers with standalone AI arm: {len(has_arm)} / {len(results)}\n")
for r in has_arm:
    print(f"  {r['title']}")
    print(f"    {r['evidence']}\n")

with open('data_v2_offline/extracted/three_arm_candidates.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=results[0].keys())
    w.writeheader()
    w.writerows(results)
print("Saved → data_v2_offline/extracted/three_arm_candidates.csv")

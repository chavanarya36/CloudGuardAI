"""Run a live scan and capture full JSON evidence for the audit."""
import requests
import json

r = requests.post(
    "http://localhost:8000/scan",
    files={"file": ("HIGH_risk.tf", open(r"D:\CloudGuardAI\data\samples\iac_files\HIGH_risk.tf", "rb"))},
    data={"scan_mode": "full"},
    timeout=120,
)
d = r.json()

with open(r"D:\CloudGuardAI\audit_scan_result.json", "w") as f:
    json.dump(d, f, indent=2, default=str)

print(f"HTTP Status: {r.status_code}")
print(f"Scan Status: {d.get('status')}")
print(f"Total findings: {d.get('total_findings')}")
print(f"Risk score: {d.get('risk_score')}")
print(f"Response keys: {list(d.keys())}")
print()

# Key ML fields at scan level
for field in ["supervised_probability", "unsupervised_probability", "ml_score",
              "rules_score", "llm_score", "scanners_used", "scanner_breakdown",
              "gnn_graph_data", "recommended_finding_order"]:
    print(f"  {field}: {json.dumps(d.get(field), default=str)[:200]}")

print()
print("=== Per-finding ML fields ===")
for i, f in enumerate(d.get("findings", [])):
    rl_action = f.get("rl_fix_action")
    rl_applied = f.get("rl_fix_applied")
    tf_fix = f.get("transformer_fix")
    tf_avail = f.get("transformer_fix_available")
    atk_path = f.get("part_of_attack_path")
    ranking = f.get("ranking_score")
    reasoning = f.get("reasoning_summary", "")[:80]
    llm_expl = (f.get("llm_explanation") or "")[:60]
    print(f"  [{i}] sev={f.get('severity'):8s} scanner={f.get('scanner'):12s} "
          f"rl={rl_action or '-':20s} rl_applied={rl_applied} "
          f"tf_avail={tf_avail} atk_path={atk_path} "
          f"ranking={ranking}")
    if tf_fix:
        print(f"       transformer_fix: {tf_fix[:80]}...")
    if reasoning:
        print(f"       reasoning: {reasoning}")

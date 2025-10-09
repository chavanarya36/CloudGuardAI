import argparse, os, json
import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score


def compute_at_threshold(y_true, y_prob, thr):
    preds = (y_prob >= thr).astype(int)
    return {
        'threshold': float(thr),
        'precision': float(precision_score(y_true, preds, zero_division=0)),
        'recall': float(recall_score(y_true, preds, zero_division=0)),
        'positives_selected': int(preds.sum())
    }


def threshold_for_top_k(y_prob, k):
    if k <= 0:
        return 1.0
    if k >= len(y_prob):
        return 0.0
    # Sort descending and take prob at position k-1
    order = np.argsort(-y_prob)
    cut_index = min(k-1, len(y_prob)-1)
    return float(y_prob[order][cut_index])


def main():
    ap = argparse.ArgumentParser(description='Tune thresholds for specific triage budgets (Top-K).')
    ap.add_argument('--predictions-dir', default='predictions_artifacts')
    ap.add_argument('--output', default='models_artifacts/threshold_budget.json')
    ap.add_argument('--budgets', nargs='*', type=int, default=[200, 500])
    args = ap.parse_args()

    pred_path = os.path.join(args.predictions_dir, 'predictions_lr.csv')
    if not os.path.exists(pred_path):
        raise SystemExit('Missing predictions_lr.csv; run prediction step first.')
    df = pd.read_csv(pred_path)
    if not {'p_has','has_findings'}.issubset(df.columns):
        raise SystemExit('predictions_lr.csv missing required columns.')

    y = df['has_findings'].values
    p = df['p_has'].values

    results = {'budgets': {}}
    for k in args.budgets:
        thr = threshold_for_top_k(p, k)
        stats = compute_at_threshold(y, p, thr)
        stats['target_top_k'] = k
        results['budgets'][str(k)] = stats

    # Also include a small sweep around each threshold (±10% relative) to illustrate sensitivity
    sweep = {}
    for k, info in results['budgets'].items():
        base_thr = info['threshold']
        rels = [0.8, 0.9, 1.0, 1.1, 1.2]
        local = []
        for r in rels:
            t = max(0.0, min(1.0, base_thr * r))
            local.append(compute_at_threshold(y, p, t))
        sweep[k] = local
    results['sensitivity'] = sweep

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    print(f'Wrote {args.output}')
    for k, info in results['budgets'].items():
        print(f"Top-{k} tuned threshold: {info['threshold']:.6f} -> precision {info['precision']:.4f}, recall {info['recall']:.4f}, positives_selected {info['positives_selected']}")

if __name__ == '__main__':
    main()

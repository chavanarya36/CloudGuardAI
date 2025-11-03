import argparse, os, json
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss


def reliability_bins(y_true, y_prob, n_bins=10):
    df = pd.DataFrame({'y': y_true, 'p': y_prob})
    # clip probabilities
    df['p'] = df['p'].clip(0, 1)
    df['bin'] = pd.qcut(df['p'], q=n_bins, duplicates='drop')
    grouped = df.groupby('bin', observed=True)
    rows = []
    for b, g in grouped:
        avg_p = g['p'].mean()
        emp = g['y'].mean() if len(g) else np.nan
        rows.append({'bin': str(b), 'count': int(len(g)), 'avg_pred': float(avg_p), 'empirical_rate': float(emp)})
    return rows


def main():
    ap = argparse.ArgumentParser(description='Compute Brier score and reliability bins for LR model.')
    ap.add_argument('--models-dir', default='models_artifacts')
    ap.add_argument('--predictions-dir', default='predictions_artifacts')
    ap.add_argument('--output-prefix', default='reliability')
    ap.add_argument('--n-bins', type=int, default=10)
    args = ap.parse_args()

    cv_path = os.path.join(args.models_dir, 'cv_metrics_lr.json')
    preds_path = os.path.join(args.predictions_dir, 'predictions_lr.csv')
    if not os.path.exists(preds_path):
        raise SystemExit('Missing predictions_lr.csv; run prediction step first.')

    preds = pd.read_csv(preds_path)
    if not {'p_has','has_findings'}.issubset(preds.columns):
        raise SystemExit('predictions_lr.csv must contain p_has and has_findings columns.')

    y = preds['has_findings'].values
    p = preds['p_has'].values.clip(0, 1)

    brier = brier_score_loss(y, p)
    bins = reliability_bins(y, p, n_bins=args.n_bins)

    report = {
        'brier_score': brier,
        'n_bins': args.n_bins,
        'total_samples': int(len(y))
    }

    json_path = os.path.join(args.models_dir, f'{args.output_prefix}_report.json')
    bins_path = os.path.join(args.models_dir, f'{args.output_prefix}_bins.csv')

    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2)
    pd.DataFrame(bins).to_csv(bins_path, index=False)

    print(f'Wrote {json_path} and {bins_path}')
    print(f"Brier Score: {brier:.6f}")

if __name__ == '__main__':
    main()

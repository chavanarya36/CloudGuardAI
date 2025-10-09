import argparse, json, os
import pandas as pd
import numpy as np


def p_at(df, k):
    if k <= 0:
        return float('nan')
    subset = df.head(k)
    if subset.empty:
        return float('nan')
    return float(subset['has_findings'].mean())


def format_float(x):
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return 'nan'
    return f"{x:.6f}" if abs(x) < 0.01 else f"{x:.4f}"


def main():
    ap = argparse.ArgumentParser(description='Summarize LR metrics and top-k precision.')
    ap.add_argument('--models-dir', default='models_artifacts')
    ap.add_argument('--predictions-dir', default='predictions_artifacts')
    ap.add_argument('--markdown', action='store_true', help='Output a Markdown table instead of plain text lines (adds both forms).')
    args = ap.parse_args()

    cv_path = os.path.join(args.models_dir, 'cv_metrics_lr.json')
    thr_path = os.path.join(args.models_dir, 'threshold_lr.json')
    pred_path = os.path.join(args.predictions_dir, 'predictions_lr.csv')

    if not os.path.exists(cv_path):
        raise SystemExit(f'Missing {cv_path}')
    if not os.path.exists(thr_path):
        raise SystemExit(f'Missing {thr_path}')
    if not os.path.exists(pred_path):
        raise SystemExit(f'Missing {pred_path}')

    with open(cv_path) as f:
        cv = json.load(f)
    with open(thr_path) as f:
        thr = json.load(f)

    preds = pd.read_csv(pred_path)
    if 'p_has' not in preds.columns or 'has_findings' not in preds.columns:
        raise SystemExit('predictions_lr.csv missing required columns p_has / has_findings')
    preds = preds.sort_values('p_has', ascending=False)

    p100 = p_at(preds, 100)
    p200 = p_at(preds, 200)
    p500 = p_at(preds, 500)

    lines = []
    lines.append(f"OOF AP: {format_float(cv.get('oof_ap'))}")
    lines.append(f"OOF ROC: {format_float(cv.get('oof_roc'))}")
    lines.append(f"OOF BalAcc: {format_float(cv.get('oof_bal_acc'))}")
    lines.append(f"Global Thr (cv_metrics): {format_float(cv.get('global_threshold'))}")
    lines.append(f"Threshold File: {format_float(thr.get('threshold_global'))}")
    fold_aps = [format_float(f.get('ap')) for f in cv.get('folds', [])]
    lines.append(f"Per-fold APs: {fold_aps}")
    lines.append(f"P@100: {format_float(p100)}")
    lines.append(f"P@200: {format_float(p200)}")
    lines.append(f"P@500: {format_float(p500)}")

    print('\n'.join(lines))

    if args.markdown:
        md_lines = []
        md_lines.append('| Metric | Value |')
        md_lines.append('|--------|-------|')
        md_lines.append(f"| OOF AP | {format_float(cv.get('oof_ap'))} |")
        md_lines.append(f"| OOF ROC | {format_float(cv.get('oof_roc'))} |")
        md_lines.append(f"| OOF BalAcc | {format_float(cv.get('oof_bal_acc'))} |")
        md_lines.append(f"| Global Threshold (cv) | {format_float(cv.get('global_threshold'))} |")
        md_lines.append(f"| Threshold (file) | {format_float(thr.get('threshold_global'))} |")
        md_lines.append(f"| Per-fold APs | {' '.join(fold_aps)} |")
        md_lines.append(f"| P@100 | {format_float(p100)} |")
        md_lines.append(f"| P@200 | {format_float(p200)} |")
        md_lines.append(f"| P@500 | {format_float(p500)} |")
        print('\nMarkdown Table:\n')
        print('\n'.join(md_lines))


if __name__ == '__main__':
    main()

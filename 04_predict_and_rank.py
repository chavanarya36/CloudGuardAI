import argparse, os, json, warnings
import numpy as np
import pandas as pd
from scipy import sparse
import joblib


def percentile_rank(values):
    order = np.argsort(values)
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.linspace(0, 100, num=len(values), endpoint=True)
    return ranks

def score_and_write(model_name, model, threshold, X, labels_df, out_dir, verbose):
    probs = model.predict_proba(X)[:,1]
    preds = (probs >= threshold).astype(int)
    include_cols = ['repo_root','rel_path','abs_path','ext','size_bytes','mtime']
    if 'has_findings' in labels_df.columns:
        include_cols.append('has_findings')
    df = labels_df[include_cols].copy()
    df['p_has'] = probs
    df['pred_has'] = preds
    df['risk_index'] = percentile_rank(probs)
    df['risk_decile'] = pd.qcut(probs, 10, labels=False, duplicates='drop') + 1
    df.sort_values('p_has', ascending=False, inplace=True)
    base = model_name.lower()
    df.to_csv(os.path.join(out_dir, f'predictions_{base}.csv'), index=False)
    df.head(100).to_csv(os.path.join(out_dir, f'top_100_{base}.csv'), index=False)
    # distribution metrics
    dist = df.copy()
    dist['decile'] = pd.qcut(dist['p_has'], 10, labels=False, duplicates='drop') + 1
    grp = dist.groupby('decile').agg({'p_has':'mean','pred_has':'sum','repo_root':'count'})
    if 'has_findings' in dist.columns:
        grp['true_pos'] = dist.groupby('decile')['has_findings'].sum()
    grp.to_csv(os.path.join(out_dir, f'dist_metrics_{base}.csv'))
    if verbose:
        print(f'[{model_name}] top 5:')
        print(df[['repo_root','rel_path','p_has']].head())
        for k in [100,200,500]:
            subset = df.head(k)
            if 'has_findings' in subset.columns:
                prec = subset['has_findings'].sum()/k
            else:
                prec = float('nan')
            print(f'[{model_name}] Precision@{k}: {prec:.4f}')


def main():
    ap = argparse.ArgumentParser(description='Predict & rank IaC file risk for multiple models.')
    ap.add_argument('--features-dir', default='features_artifacts')
    ap.add_argument('--labels-file', default='labels_artifacts/iac_labels_clean.csv')
    ap.add_argument('--models-dir', default='models_artifacts')
    ap.add_argument('--output-dir', default='predictions_artifacts')
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    X = sparse.load_npz(os.path.join(args.features_dir,'X_all.npz'))
    labels_df = pd.read_csv(args.labels_file)

    # Load LR
    lr_model_path = os.path.join(args.models_dir,'best_model_lr.joblib')
    if not os.path.exists(lr_model_path):
        raise FileNotFoundError('best_model_lr.joblib not found')
    lr_model = joblib.load(lr_model_path)
    with open(os.path.join(args.models_dir,'threshold_lr.json')) as f:
        lr_thr = json.load(f)['threshold_global']
    score_and_write('LR', lr_model, lr_thr, X, labels_df, args.output_dir, args.verbose)

    # Load LGBM if present
    lgbm_path = os.path.join(args.models_dir,'best_model_lgbm.joblib')
    if os.path.exists(lgbm_path):
        try:
            lgbm_model = joblib.load(lgbm_path)
            with open(os.path.join(args.models_dir,'threshold_lgbm.json')) as f:
                lgbm_thr = json.load(f)['threshold_global']
            score_and_write('LGBM', lgbm_model, lgbm_thr, X, labels_df, args.output_dir, args.verbose)
        except Exception as e:
            warnings.warn(f'Failed scoring LGBM model: {e}')

    # Backward-compatible single-file copies (optional)
    if os.path.exists(os.path.join(args.output_dir,'predictions_lr.csv')):
        import shutil
        shutil.copy(os.path.join(args.output_dir,'predictions_lr.csv'), os.path.join(args.output_dir,'predictions.csv'))
        if os.path.exists(os.path.join(args.output_dir,'top_100_lr.csv')):
            shutil.copy(os.path.join(args.output_dir,'top_100_lr.csv'), os.path.join(args.output_dir,'top_100.csv'))

if __name__ == '__main__':
    main()

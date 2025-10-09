import argparse, os, json
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score


def load_data(features_dir, labels_file):
    X = sparse.load_npz(os.path.join(features_dir, 'X_all.npz'))
    y = np.load(os.path.join(features_dir, 'y.npy'))
    labels_df = pd.read_csv(labels_file)
    if len(labels_df) != X.shape[0]:
        raise ValueError('Mismatch between features and labels rows')
    return X, y, labels_df


def per_repo_leave_one_positive_out(X, y, labels_df, max_iter=200):
    repo_col = 'repo_root'
    repos = labels_df[repo_col].astype(str).values
    pos_repos = np.unique(repos[y == 1])
    results = []
    for r in pos_repos:
        test_mask = (repos == r)
        if test_mask.sum() == 0:
            continue
        X_tr = X[~test_mask]
        y_tr = y[~test_mask]
        X_te = X[test_mask]
        y_te = y[test_mask]
        # If training set collapses to single class, record skipped evaluation
        if len(np.unique(y_tr)) < 2:
            results.append({
                'held_out_repo': r,
                'n_test': int(test_mask.sum()),
                'n_pos_test': int(y_te.sum()),
                'ap': float('nan'),
                'roc': float('nan'),
                'status': 'skipped_single_class_training'
            })
            continue
        # Basic LR (no calibration for speed); reuse production hyperparam C=0.3
        model = LogisticRegression(C=0.3, class_weight='balanced', max_iter=max_iter, solver='liblinear', random_state=42)
        model.fit(X_tr, y_tr)
        prob_te = model.predict_proba(X_te)[:,1]
        ap = average_precision_score(y_te, prob_te) if y_te.sum() > 0 else float('nan')
        roc = roc_auc_score(y_te, prob_te) if y_te.sum() > 0 and len(np.unique(y_te))>1 else float('nan')
        results.append({
            'held_out_repo': r,
            'n_test': int(test_mask.sum()),
            'n_pos_test': int(y_te.sum()),
            'ap': ap,
            'roc': roc,
            'status': 'ok'
        })
    return results


def main():
    ap = argparse.ArgumentParser(description='Per-repo leave-one-positive-repo-out validation.')
    ap.add_argument('--features-dir', default='features_artifacts')
    ap.add_argument('--labels-file', default='labels_artifacts/iac_labels_clean.csv')
    ap.add_argument('--output', default='models_artifacts/per_repo_metrics.json')
    args = ap.parse_args()

    X, y, labels_df = load_data(args.features_dir, args.labels_file)
    results = per_repo_leave_one_positive_out(X, y, labels_df)
    summary = {
        'n_positive_repos': len({r['held_out_repo'] for r in results}),
        'results': results
    }
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'Wrote {args.output} with {len(results)} held-out evaluations.')

if __name__ == '__main__':
    main()

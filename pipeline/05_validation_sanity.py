import argparse, os, json, numpy as np, pandas as pd
from scipy import sparse
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sklearn.metrics import average_precision_score, balanced_accuracy_score, roc_auc_score
import joblib


def _group_split_or_strat(X, y, groups, splits):
    unique_groups = np.unique(groups)
    n_splits = min(splits, len(unique_groups))
    pos_groups = np.unique(groups[y==1])
    if len(pos_groups) == 1:
        # fallback stratified
        skf = StratifiedKFold(n_splits=min(5, max(2, int(y.sum()) if y.sum()>=2 else 2)), shuffle=True, random_state=42)
        for tr, va in skf.split(X, y):
            yield tr, va
    else:
        gkf = GroupKFold(n_splits=n_splits)
        for tr, va in gkf.split(X, y, groups):
            yield tr, va

def shuffled_baseline(X, y, groups, splits):
    y_shuf = y.copy()
    rng = np.random.default_rng(42)
    rng.shuffle(y_shuf)
    scores = []
    for tr, va in _group_split_or_strat(X, y_shuf, groups, splits):
        model = LogisticRegression(class_weight='balanced', max_iter=200, solver='saga', n_jobs=-1)
        model.fit(X[tr], y_shuf[tr])
        probs = model.predict_proba(X[va])[:,1]
        ap = average_precision_score(y_shuf[va], probs)
        scores.append(ap)
    return float(np.mean(scores)), float(np.std(scores))


def ablation_dense_only(X, y, groups, dense_offset, splits):
    scores = []
    bals = []
    for tr, va in _group_split_or_strat(X, y, groups, splits):
        X_tr = X[tr][:, dense_offset:]
        X_va = X[va][:, dense_offset:]
        model = LogisticRegression(class_weight='balanced', max_iter=200, solver='saga', n_jobs=-1)
        model.fit(X_tr, y[tr])
        probs = model.predict_proba(X_va)[:,1]
        ap = average_precision_score(y[va], probs)
        preds = (probs >= 0.5).astype(int)
        bal = balanced_accuracy_score(y[va], preds)
        scores.append(ap)
        bals.append(bal)
    return float(np.mean(scores)), float(np.std(scores)), float(np.mean(bals))


def full_model_cv(X, y, groups, splits):
    scores = []
    for tr, va in _group_split_or_strat(X, y, groups, splits):
        model = LogisticRegression(class_weight='balanced', max_iter=200, solver='saga', n_jobs=-1)
        model.fit(X[tr], y[tr])
        probs = model.predict_proba(X[va])[:,1]
        ap = average_precision_score(y[va], probs)
        scores.append(ap)
    return float(np.mean(scores))


def main():
    ap = argparse.ArgumentParser(description='Sanity validation: shuffled baseline, ablation, and model family comparison.')
    ap.add_argument('--features-dir', default='features_artifacts')
    ap.add_argument('--labels-file', default='labels_artifacts/iac_labels_clean.csv')
    ap.add_argument('--models-dir', default='models_artifacts')
    ap.add_argument('--cv-splits', type=int, default=5)
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()

    X = sparse.load_npz(os.path.join(args.features_dir,'X_all.npz'))
    y = np.load(os.path.join(args.features_dir,'y.npy'))
    labels_df = pd.read_csv(args.labels_file)
    groups = labels_df['repo_root'].astype(str).values

    import json as _json
    with open(os.path.join(args.features_dir,'meta.json')) as f:
        meta = _json.load(f)
    dense_offset = meta['dense_feature_offset']

    if args.verbose:
        print('Running shuffled baseline...')
    shuf_mean, shuf_std = shuffled_baseline(X, y, groups, args.cv_splits)

    if args.verbose:
        print('Running full model AP (quick CV)...')
    full_ap = full_model_cv(X, y, groups, args.cv_splits)

    if args.verbose:
        print('Running ablation (dense only)...')
    abl_ap_mean, abl_ap_std, abl_bal = ablation_dense_only(X, y, groups, dense_offset, args.cv_splits)

    report = {
        'prevalence': float(y.mean()),
        'shuffled_ap_mean': shuf_mean,
        'shuffled_ap_std': shuf_std,
        'full_ap_mean': full_ap,
        'ablation_dense_only_ap_mean': abl_ap_mean,
        'ablation_dense_only_ap_std': abl_ap_std,
        'ablation_dense_only_bal_acc': abl_bal,
        'leakage_suspected': full_ap < (shuf_mean + 0.01)
    }
    # Model family comparison (if artifacts exist)
    comparisons = []
    # Helper to load threshold
    def _load_thr(path):
        try:
            with open(path) as f:
                return json.load(f)['threshold_global']
        except Exception:
            return 0.5
    # LR
    lr_path = os.path.join(args.models_dir,'best_model_lr.joblib')
    if os.path.exists(lr_path):
        lr_model = joblib.load(lr_path)
        thr_lr = _load_thr(os.path.join(args.models_dir,'threshold_lr.json'))
        probs_lr = lr_model.predict_proba(X)[:,1]
        ap_lr = average_precision_score(y, probs_lr)
        roc_lr = roc_auc_score(y, probs_lr) if y.sum()>0 else float('nan')
        preds_lr = (probs_lr >= thr_lr).astype(int)
        bal_lr = balanced_accuracy_score(y, preds_lr)
        comparisons.append({'family':'lr','ap':ap_lr,'roc':roc_lr,'bal_acc':bal_lr,'threshold':thr_lr})
    # LGBM
    lgbm_path = os.path.join(args.models_dir,'best_model_lgbm.joblib')
    if os.path.exists(lgbm_path):
        try:
            lgbm_model = joblib.load(lgbm_path)
            thr_lgbm = _load_thr(os.path.join(args.models_dir,'threshold_lgbm.json'))
            probs_lgbm = lgbm_model.predict_proba(X)[:,1]
            ap_lgbm = average_precision_score(y, probs_lgbm)
            roc_lgbm = roc_auc_score(y, probs_lgbm) if y.sum()>0 else float('nan')
            preds_lgbm = (probs_lgbm >= thr_lgbm).astype(int)
            bal_lgbm = balanced_accuracy_score(y, preds_lgbm)
            comparisons.append({'family':'lgbm','ap':ap_lgbm,'roc':roc_lgbm,'bal_acc':bal_lgbm,'threshold':thr_lgbm})
        except Exception as e:
            if args.verbose:
                print('Failed LGBM comparison:', e)
    if comparisons:
        comp_df = pd.DataFrame(comparisons)
        comp_df.to_csv('sanity_comparison.csv', index=False)
        report['model_families_compared'] = True
        report['best_family_by_ap'] = comp_df.sort_values('ap').iloc[-1]['family']
    else:
        report['model_families_compared'] = False
    with open('sanity_report.json','w') as f:
        json.dump(report, f, indent=2)

    if args.verbose:
        print('--- Sanity Report ---')
        for k,v in report.items():
            print(f'{k}: {v}')
        if report['leakage_suspected']:
            print('WARNING: Full AP too close to shuffled baseline -> potential leakage or weak signal.')
        else:
            print('PASS: Signal above shuffled baseline.')

if __name__ == '__main__':
    main()

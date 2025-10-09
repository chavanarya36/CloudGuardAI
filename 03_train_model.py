import argparse, os, json, warnings
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score, balanced_accuracy_score
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sklearn.calibration import CalibratedClassifierCV
import joblib

# Clean LR-only training script (liblinear + sigmoid calibration)


def precision_at_k(y_true, y_scores, k):
    if k <= 0:
        return 0.0
    order = np.argsort(-y_scores)
    topk = order[:k]
    return float(y_true[topk].sum()) / k


def choose_threshold_balanced(y_true, y_scores):
    # Evaluate thresholds from precision-recall curve prob grid (sorted unique scores) for balanced accuracy
    thresholds = np.unique(np.clip(y_scores, 0, 1))
    best_thr = 0.5
    best_bal = -1
    for t in thresholds:
        preds = (y_scores >= t).astype(int)
        if preds.sum() == 0:
            # avoid division issue if all negatives
            bal = balanced_accuracy_score(y_true, preds)
        else:
            bal = balanced_accuracy_score(y_true, preds)
        if bal > best_bal:
            best_bal = bal
            best_thr = t
    return float(best_thr), float(best_bal)


def train_lr(C):
    return LogisticRegression(C=C, class_weight='balanced', max_iter=200, solver='liblinear', random_state=42)


def calibrate_model(model, X_tr, y_tr):
    """Calibrate probability outputs with 5-fold Platt scaling (sigmoid).

    Returns (fitted_model, calibration_label). If insufficient positives, returns
    the original model uncalibrated.
    """
    if y_tr.sum() < 2:
        return model, 'none'
    cal = CalibratedClassifierCV(model, cv=5, method='sigmoid')
    return cal.fit(X_tr, y_tr), 'sigmoid_cv5'


def generate_splits(X, y, groups, desired_splits):
    unique_groups = np.unique(groups)
    pos_groups = np.unique(groups[y==1])
    if len(pos_groups) == 1:
        n_splits = 5 if y.sum() >= 5 else 3
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        for tr, va in skf.split(X, y):
            yield 'skf', tr, va
    else:
        n_splits = min(desired_splits, len(unique_groups))
        if n_splits < 2:
            raise ValueError('Not enough groups for CV')
        gkf = GroupKFold(n_splits=n_splits)
        for tr, va in gkf.split(X, y, groups):
            yield 'gkf', tr, va


def evaluate_family(model, X_val, y_val):
    probs = model.predict_proba(X_val)[:,1]
    ap = average_precision_score(y_val, probs)
    roc = roc_auc_score(y_val, probs) if y_val.sum()>0 else float('nan')
    thr, bal = choose_threshold_balanced(y_val, probs)
    p100 = precision_at_k(y_val, probs, 100)
    p200 = precision_at_k(y_val, probs, 200)
    p500 = precision_at_k(y_val, probs, 500)
    return probs, {'ap': ap, 'roc': roc, 'bal_acc': bal, 'threshold': thr, 'p@100': p100, 'p@200': p200, 'p@500': p500}


def cross_validate_model(args, X, y, groups, export_folds=None):
    param_grid = [{'C': c} for c in [0.1, 0.3, 1.0]]
    folds = []
    oof_scores = np.zeros_like(y, dtype=float)
    thresholds = []
    fold_splits = []
    for fold_id, (mode, tr, va) in enumerate(generate_splits(X, y, groups, args.cv_splits), start=1):
        X_tr, X_val = X[tr], X[va]
        y_tr, y_val = y[tr], y[va]
        best_metric = -1
        best_record = None
        best_probs = None
        for params in param_grid:
            base = train_lr(params['C'])
            cal_model, used_method = calibrate_model(base, X_tr, y_tr)
            probs, metrics = evaluate_family(cal_model, X_val, y_val)
            metrics['calibration'] = used_method
            metrics['params'] = params
            metrics['fold'] = fold_id
            metrics['cv_mode'] = mode
            if metrics['ap'] > best_metric:
                best_metric = metrics['ap']
                best_record = metrics
                best_probs = probs
        oof_scores[va] = best_probs
        thresholds.append(best_record['threshold'])
        folds.append(best_record)
        fold_splits.append({'fold': fold_id, 'mode': mode, 'train_indices': tr.tolist(), 'val_indices': va.tolist()})
    global_thr = float(np.clip(np.mean(thresholds), 0.001, 0.999))
    oof_ap = average_precision_score(y, oof_scores)
    oof_roc = roc_auc_score(y, oof_scores) if y.sum()>0 else float('nan')
    oof_preds = (oof_scores >= global_thr).astype(int)
    oof_bal = balanced_accuracy_score(y, oof_preds)
    summary = {
        'folds': folds,
        'oof_ap': oof_ap,
        'oof_roc': oof_roc,
        'oof_bal_acc': oof_bal,
        'global_threshold': global_thr,
        'family': 'lr'
    }
    folds_df = pd.DataFrame(folds)
    best_params_row = folds_df.sort_values('ap').iloc[-1]
    best_params = best_params_row['params']
    full_base = train_lr(best_params['C'])
    full_model, _ = calibrate_model(full_base, X, y)
    if export_folds is not None:
        with open(export_folds,'w') as f:
            json.dump({'family': 'lr', 'fold_splits': fold_splits}, f, indent=2)
    return full_model, summary


def write_json(path, obj):
    with open(path,'w') as f:
        json.dump(obj, f, indent=2)


def main():
    ap = argparse.ArgumentParser(description='Train Logistic Regression (liblinear) with sigmoid calibration (CV=3).')
    ap.add_argument('--features-dir', default='features_artifacts')
    ap.add_argument('--labels-file', default='labels_artifacts/iac_labels_clean.csv')
    ap.add_argument('--output-dir', default='models_artifacts')
    ap.add_argument('--cv-splits', type=int, default=5)
    ap.add_argument('--calibrate', choices=['auto','isotonic','sigmoid','none'], default='auto')
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    X = sparse.load_npz(os.path.join(args.features_dir,'X_all.npz'))
    y = np.load(os.path.join(args.features_dir,'y.npy'))
    labels_df = pd.read_csv(args.labels_file)
    if len(labels_df) != X.shape[0]:
        raise ValueError('Row mismatch between labels and feature matrix')
    groups = labels_df['repo_root'].astype(str).values

    lr_model, lr_summary = cross_validate_model(args, X, y, groups, export_folds=os.path.join(args.output_dir,'cv_folds_lr.json'))
    joblib.dump(lr_model, os.path.join(args.output_dir,'best_model_lr.joblib'))
    write_json(os.path.join(args.output_dir,'threshold_lr.json'), {'threshold_global': lr_summary['global_threshold']})
    write_json(os.path.join(args.output_dir,'cv_metrics_lr.json'), lr_summary)

    if args.verbose:
        print('[LR] OOF AP:', round(lr_summary['oof_ap'],4), 'ROC:', round(lr_summary['oof_roc'],4), 'BalAcc:', round(lr_summary['oof_bal_acc'],4), 'Thr:', round(lr_summary['global_threshold'],4))

if __name__ == '__main__':
    main()

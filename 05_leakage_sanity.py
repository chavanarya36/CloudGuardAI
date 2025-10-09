import argparse, os, json
import numpy as np
import pandas as pd
from sklearn.feature_extraction import FeatureHasher
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.model_selection import GroupShuffleSplit
from scipy.sparse import hstack, csr_matrix

def simple_features(df: pd.DataFrame):
    if "basename" not in df.columns:
        base_src = None
        for cand in ["file", "rel_path", "file_path", "abs_path"]:
            if cand in df.columns:
                base_src = cand
                break
        if base_src is None:
            df["basename"] = ""
        else:
            df["basename"] = df[base_src].astype(str).map(os.path.basename)

    toks = (
        df["basename"].astype(str)
        .str.lower()
        .str.replace(r"[^a-z0-9]+", " ", regex=True)
        .str.split()
        .apply(lambda xs: {f"t={w}": 1 for w in xs})
    )
    H = FeatureHasher(n_features=2**14, input_type="dict").transform(toks.tolist())
    size = df.get("size_bytes", pd.Series([0] * len(df))).fillna(0).astype(float).values.reshape(-1, 1)
    lines = df.get("lines", pd.Series([0] * len(df))).fillna(0).astype(float).values.reshape(-1, 1)
    return hstack([H, size, lines])

def ap_eval(X, y, groups):
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    tr, te = next(splitter.split(np.zeros(len(y)), y, groups))
    clf = LogisticRegression(max_iter=300, class_weight="balanced")
    clf.fit(X[tr], y[tr])
    proba = clf.predict_proba(X[te])[:, 1]
    return average_precision_score(y[te], proba)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels-file", required=True)
    ap.add_argument("--out-json", default="sanity_report.json")
    args = ap.parse_args()

    try:
        df = pd.read_csv(args.labels_file)
    except FileNotFoundError:
        print(f"Error: The file '{args.labels_file}' does not exist.")
        return
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{args.labels_file}' is empty or invalid.")
        return
    except Exception as e:
        print(f"Error: Failed to read the file '{args.labels_file}'. Details: {e}")
        return
    if "has_findings" not in df.columns:
        print("Missing has_findings column.")
        return

    y = (df["has_findings"] > 0).astype(int).values
    if y.sum() == 0:
        print("All negatives; fix Step-01 first.")
        return

    if "repo_root_canon" in df.columns:
        groups = df["repo_root_canon"].astype(str).values
    elif "repo" in df.columns:
        groups = df["repo"].astype(str).values
    else:
        groups = np.arange(len(df))

    X = simple_features(df)
    ap_normal = ap_eval(X, y, groups)

    y_shuf = y.copy()
    rng = np.random.default_rng(0)
    rng.shuffle(y_shuf)
    ap_shuffled = ap_eval(X, y_shuf, groups)

    size = df.get("size_bytes", pd.Series([0]*len(df))).fillna(0).astype(float).values.reshape(-1,1)
    lines = df.get("lines", pd.Series([0]*len(df))).fillna(0).astype(float).values.reshape(-1,1)
    X_abl = csr_matrix(np.hstack([size, lines]))
    ap_abl = ap_eval(X_abl, y, groups)

    prevalence = float(y.mean())
    report = {
        "prevalence": prevalence,
        "AP_normal": float(ap_normal),
        "AP_shuffled": float(ap_shuffled),
        "AP_ablation_size_lines_only": float(ap_abl),
        "interpretation": {
            "AP_normal_vs_prevalence": "AP_normal >> prevalence indicates useful signal.",
            "AP_shuffled": "Should ≈ prevalence (else leakage).",
            "Ablation_drop": "AP_normal - ablation > 0 means tokens add value."
        }
    }
    with open(args.out_json, "w") as f:
        json.dump(report, f, indent=2)
    print("✅ sanity_report:", report)

if __name__ == "__main__":
    main()
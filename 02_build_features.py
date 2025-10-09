import argparse
import os
import json
import re
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import sparse
from sklearn.feature_extraction import FeatureHasher


def log1p_arr(x):
    return np.log1p(np.asarray(x, dtype=float))


SEG_SPLIT_RE = re.compile(r"[\\/._\-]+")


def char_ngrams(s: str, n: int = 3, prefix: str = 'c3:'):
    s = s.lower()
    if len(s) < n:
        return []
    return [f"{prefix}{s[i:i+n]}" for i in range(len(s)-n+1)]


def path_tokens(repo_root: str, rel_path: str, ext: str):
    toks = []
    rel = str(rel_path) if not pd.isna(rel_path) else ''
    root = str(repo_root) if not pd.isna(repo_root) else ''
    base = Path(rel).name.lower() if rel else ''
    stem = base.rsplit('.',1)[0] if '.' in base else base

    # Segments
    segs = [s for s in SEG_SPLIT_RE.split(rel.lower()) if s]
    for s in segs:
        toks.append(f"seg:{s}")
    # 2-grams of segments
    for i in range(len(segs)-1):
        toks.append(f"seg2:{segs[i]}+{segs[i+1]}")
    # basename char 3-grams
    toks.extend(char_ngrams(base, 3))
    # extension token
    # ensure extension is a string (ext column contains leading dot or empty)
    if isinstance(ext, float):  # NaN
        ext_clean = ''
    else:
        ext_clean = str(ext or '').lower()
    if ext_clean:
        toks.append(f"ext={ext_clean}")
    # flags
    low_rel = rel.lower()
    if ext_clean == '.tf':
        toks.append('flag:is_tf')
    if ext_clean in ('.yaml', '.yml'):
        toks.append('flag:is_yaml')
    if ext_clean == '.json':
        toks.append('flag:is_json')
    if ext_clean == '.bicep':
        toks.append('flag:is_bicep')
    if 'k8s' in low_rel or 'chart' in low_rel:
        toks.append('flag:is_k8s')
    return toks, stem


def build_sparse(df: pd.DataFrame, hash_dim: int):
    dicts = []
    stems = []
    for repo_root, rel_path, ext in zip(df['repo_root'], df['rel_path'], df.get('ext', ['']*len(df))):
        toks, stem = path_tokens(repo_root, rel_path, ext)
        stems.append(stem)
        d = {}
        for t in toks:
            d[t] = d.get(t,0) + 1
        dicts.append(d)
    hasher = FeatureHasher(n_features=hash_dim, input_type='dict', alternate_sign=False)
    X = hasher.transform(dicts)
    return X, stems


RESOURCE_PATTERNS = [
    ('aws_s3_bucket', re.compile(r'aws_s3_bucket')),
    ('aws_iam_policy', re.compile(r'aws_iam_policy')),
    ('aws_security_group', re.compile(r'aws_security_group')),
    ('aws_iam_role', re.compile(r'aws_iam_role')),
    ('aws_lambda_function', re.compile(r'aws_lambda_function')),
    ('k8s_deployment', re.compile(r'(?i)kind:\s*deployment')),
    ('k8s_service', re.compile(r'(?i)kind:\s*service')),
    ('terraform_module', re.compile(r'(?i)module\s+"')),
    ('terraform_variable', re.compile(r'(?i)variable\s+"')),
]


def extract_resource_counts(row, enable=False, cache_dir=None):
    if not enable:
        return {}
    path = row.get('abs_path') or ''
    rel = row.get('rel_path') or ''
    content = ''
    counts = {}
    if path and os.path.isfile(path):
        try:
            with open(path, 'r', errors='ignore') as f:
                content = f.read(120000)  # cap read
        except Exception:
            content = ''
    haystack = (rel.lower() + '\n' + content)
    for name, pat in RESOURCE_PATTERNS:
        counts[name] = len(pat.findall(haystack))
    return counts


def build_dense(df: pd.DataFrame, stems, use_resource_tokens: bool):
    cols = []
    names = []
    # size_bytes
    size = df.get('size_bytes')
    if size is not None:
        cols.append(log1p_arr(size).reshape(-1,1))
        names.append('log_size_bytes')
    # lines (may be missing)
    lines = df.get('lines')
    if lines is None:
        lines_arr = np.zeros((len(df),1))
    else:
        lines_arr = log1p_arr(lines).reshape(-1,1)
    cols.append(lines_arr)
    names.append('log_lines')
    # path depth
    depth = df['rel_path'].fillna('').apply(lambda s: str(s).count('/') + str(s).count('\\'))
    cols.append(depth.values.reshape(-1,1))
    names.append('path_depth')
    # flags
    rel_lower = df['rel_path'].fillna('').str.lower()
    example_flag = rel_lower.str.contains('example|samples|demo', regex=True).astype(int).values.reshape(-1,1)
    test_flag = rel_lower.str.contains('test|spec', regex=True).astype(int).values.reshape(-1,1)
    ci_flag = rel_lower.str.contains('\/.github\/|\.gitlab-ci', regex=True).astype(int).values.reshape(-1,1)
    cols.extend([example_flag, test_flag, ci_flag])
    names.extend(['is_example','is_test','is_ci'])
    # stem len + log
    stem_lens = np.array([len(s) for s in stems], dtype=float).reshape(-1,1)
    cols.append(stem_lens)
    names.append('stem_len')
    cols.append(log1p_arr(stem_lens))
    names.append('log_stem_len')
    # extension one-hot limited categories
    exts = df.get('ext', pd.Series(['']*len(df))).fillna('').str.lower()
    def ext_cat(e):
        if e == '.tf': return 'tf'
        if e in ('.yaml','.yml'): return 'yaml'
        if e == '.json': return 'json'
        if e == '.bicep': return 'bicep'
        return 'other'
    cat = exts.apply(ext_cat)
    for c in ['tf','yaml','json','bicep','other']:
        cols.append((cat==c).astype(int).values.reshape(-1,1))
        names.append(f'ext_{c}')
    # resource token counts (optional)
    resource_feature_names = []
    if use_resource_tokens:
        res_rows = []
        for idx, row in df.iterrows():
            res_rows.append(extract_resource_counts(row, enable=True))
        # collect arrays preserving order
        for feat_name, _ in RESOURCE_PATTERNS:
            arr = np.array([r.get(feat_name,0) for r in res_rows], dtype=float).reshape(-1,1)
            cols.append(arr)
            names.append(f'resource_{feat_name}')
            resource_feature_names.append(f'resource_{feat_name}')
    dense = np.hstack(cols)
    return dense, names, resource_feature_names


def main():
    ap = argparse.ArgumentParser(description='Advanced feature builder (hash tokens + dense).')
    ap.add_argument('--labels-file', default='labels_artifacts/iac_labels_clean.csv')
    ap.add_argument('--output-dir', default='features_artifacts')
    ap.add_argument('--hash-dim', type=int, default=32768)
    ap.add_argument('--preview', type=int, default=50)
    ap.add_argument('--use-resource-tokens', action='store_true', help='Parse file contents for IaC resource pattern counts.')
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    if args.verbose:
        print('Loading labels...')
    df = pd.read_csv(args.labels_file)
    n = len(df)
    if args.verbose:
        print(f'Rows: {n:,}')
    if 'has_findings' not in df.columns:
        raise ValueError('labels file missing has_findings')
    y = df['has_findings'].astype(int).values

    if args.verbose:
        print('Building sparse hashed tokens...')
    X_sparse, stems = build_sparse(df, args.hash_dim)
    if args.verbose:
        print('Sparse shape:', X_sparse.shape)

    if args.verbose:
        print('Building dense features...')
    X_dense, dense_names, resource_names = build_dense(df, stems, args.use_resource_tokens)
    dense_offset = X_sparse.shape[1]
    X_all = sparse.hstack([X_sparse, sparse.csr_matrix(X_dense)], format='csr')

    nnz = X_all.nnz
    density = nnz / (X_all.shape[0] * X_all.shape[1])

    # Save artifacts
    sparse.save_npz(os.path.join(args.output_dir, 'X_all.npz'), X_all)
    np.save(os.path.join(args.output_dir, 'y.npy'), y)
    meta = {
        'hash_dim': args.hash_dim,
        'n_samples': int(X_all.shape[0]),
        'n_features_sparse': int(X_sparse.shape[1]),
        'n_features_dense': int(X_dense.shape[1]),
        'n_features_total': int(X_all.shape[1]),
        'dense_feature_offset': dense_offset,
        'dense_feature_names': dense_names,
        'resource_feature_names': resource_names,
        'sparse_nnz': int(nnz),
        'sparse_density': density,
        'positive_count': int(y.sum()),
        'positive_prevalence': float(y.mean()),
        'token_spec': 'segments + seg 2-grams + basename char3 + ext token + flag tokens'
    }
    with open(os.path.join(args.output_dir, 'meta.json'), 'w') as f:
        json.dump(meta, f, indent=2)

    # Preview
    preview_rows = min(args.preview, X_all.shape[0])
    rows = []
    for i in range(preview_rows):
        row = X_all.getrow(i)
        rows.append({
            'row': i,
            'repo_root': df.loc[i, 'repo_root'],
            'rel_path': df.loc[i, 'rel_path'],
            'ext': df.loc[i, 'ext'],
            'size_bytes': df.loc[i, 'size_bytes'],
            'nnz': int(row.nnz)
        })
    pd.DataFrame(rows).to_csv(os.path.join(args.output_dir, 'features_preview.csv'), index=False)

    if args.verbose:
        print(f"Final shape: {X_all.shape[0]} x {X_all.shape[1]}")
        print(f"NNZ: {nnz} (density {density:.4%})")
        print(f"Positives: {y.sum()} ({y.mean():.4%})")
        print('Saved X_all.npz, y.npy, meta.json, features_preview.csv')

if __name__ == '__main__':
    main()

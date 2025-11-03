import argparse
import os
import sys
import pandas as pd
from pathlib import Path

# ---------------- Canonicalization Utilities ---------------- #

def norm_path(p: str) -> str:
    if pd.isna(p) or p is None:
        return ''
    p = str(p).strip().replace('\\', '/').lower()
    # strip drive letters like d:/
    if len(p) > 2 and p[1] == ':' and p[2] == '/':
        p = p[3:]
    # collapse duplicate slashes
    while '//' in p:
        p = p.replace('//', '/')
    return p

def repo_root_canon_from_fullpath(p: str) -> str:
    p = norm_path(p)
    # heuristic: repo root is iac_subset/<topdir>
    marker = 'iac_subset/'
    if marker in p:
        after = p.split(marker, 1)[1]
        parts = after.split('/')
        if parts:
            return marker + parts[0]
    # fallback: first two segments
    segs = [s for s in p.split('/') if s]
    return '/'.join(segs[:2]) if len(segs) >= 2 else (segs[0] if segs else '')

def make_join_key(abs_norm: str) -> str:
    # full normalized absolute path preferred
    return abs_norm

SEVERITY_BUCKETS = ['critical', 'high', 'medium', 'low']

# ---------------- Core Processing ---------------- #

def load_inventory(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # normalize absolute path
    if 'abs_path' not in df.columns:
        raise ValueError('inventory missing abs_path column')
    df['abs_norm'] = df['abs_path'].apply(norm_path)
    df['repo_root_canon'] = df['abs_path'].apply(repo_root_canon_from_fullpath)
    df['basename'] = df['abs_path'].apply(lambda x: Path(str(x)).name.lower())
    df['join_key_primary'] = df['abs_norm'].apply(make_join_key)
    df['join_key_fallback'] = df['repo_root_canon'] + '||' + df['basename']
    return df

def load_checkov(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # expected columns: file_abs_path, severity (may be empty)
    file_col = None
    for cand in ['file_abs_path', 'file', 'abs_path']:
        if cand in df.columns:
            file_col = cand
            break
    if file_col is None:
        raise ValueError('No file path column found in checkov file.')
    df['file_abs_path_original'] = df[file_col]
    df['abs_norm'] = df[file_col].apply(norm_path)
    df['repo_root_canon'] = df[file_col].apply(repo_root_canon_from_fullpath)
    df['basename'] = df[file_col].apply(lambda x: Path(str(x)).name.lower())
    df['join_key_primary'] = df['abs_norm'].apply(make_join_key)
    df['join_key_fallback'] = df['repo_root_canon'] + '||' + df['basename']
    # normalize severities to lowercase canonical buckets
    if 'severity' in df.columns:
        df['severity'] = df['severity'].fillna('').str.lower().str.strip()
        df.loc[~df['severity'].isin(SEVERITY_BUCKETS), 'severity'] = ''
    else:
        df['severity'] = ''
    return df

def aggregate_checkov(df: pd.DataFrame) -> pd.DataFrame:
    # raw counts by file (primary key)
    grp = df.groupby('join_key_primary')
    agg_rows = []
    for key, g in grp:
        raw_total = len(g)
        sev_counts = {s: 0 for s in SEVERITY_BUCKETS}
        if 'severity' in g.columns:
            vc = g['severity'].value_counts()
            for sev, cnt in vc.items():
                if sev in sev_counts:
                    sev_counts[sev] = int(cnt)
        bucket_sum = sum(sev_counts.values())
        if bucket_sum == 0 and raw_total > 0:
            # promote to low (fallback)
            sev_counts['low'] = raw_total
            bucket_sum = raw_total
        num_findings = max(bucket_sum, raw_total)
        agg_rows.append({
            'join_key_primary': key,
            'raw_total': raw_total,
            **{f'severity_{s}': sev_counts[s] for s in SEVERITY_BUCKETS},
            'num_findings': num_findings,
            'has_findings': 1 if num_findings > 0 else 0,
        })
    agg_df = pd.DataFrame(agg_rows)
    return agg_df

def rekey_for_fallback(df: pd.DataFrame) -> pd.DataFrame:
    # create fallback aggregation keyed by (repo_root_canon||basename)
    grp = df.groupby('join_key_fallback')
    rows = []
    for key, g in grp:
        raw_total = g['raw_total'].sum() if 'raw_total' in g.columns else len(g)
        sev_counts = {s: g[f'severity_{s}'].sum() if f'severity_{s}' in g.columns else 0 for s in SEVERITY_BUCKETS}
        bucket_sum = sum(sev_counts.values())
        if bucket_sum == 0 and raw_total > 0:
            sev_counts['low'] = raw_total
            bucket_sum = raw_total
        num_findings = max(bucket_sum, raw_total)
        rows.append({
            'join_key_fallback': key,
            'raw_total_fb': raw_total,
            **{f'severity_{s}_fb': sev_counts[s] for s in SEVERITY_BUCKETS},
            'num_findings_fb': num_findings,
            'has_findings_fb': 1 if num_findings > 0 else 0,
        })
    return pd.DataFrame(rows)

def merge_labels(inv: pd.DataFrame, agg_primary: pd.DataFrame, agg_fb: pd.DataFrame) -> pd.DataFrame:
    df = inv.merge(agg_primary, on='join_key_primary', how='left')
    # rows without findings attempt fallback merge
    need_fb = df['num_findings'].isna()
    if need_fb.any():
        df = df.merge(agg_fb, on='join_key_fallback', how='left')
        # fill primary with fallback where primary missing
        for col in ['raw_total', 'num_findings', 'has_findings'] + [f'severity_{s}' for s in SEVERITY_BUCKETS]:
            if col in df.columns:
                fb_col = None
                if col in ['raw_total']:
                    fb_col = 'raw_total_fb'
                elif col in ['num_findings']:
                    fb_col = 'num_findings_fb'
                elif col in ['has_findings']:
                    fb_col = 'has_findings_fb'
                elif col.startswith('severity_'):
                    sev = col.split('_',1)[1]
                    fb_col = f'severity_{sev}_fb'
                if fb_col and fb_col in df.columns:
                    df[col] = df[col].fillna(df[fb_col])
        # cleanup fb helper columns
        fb_cols = [c for c in df.columns if c.endswith('_fb')]
        df.drop(columns=fb_cols, inplace=True, errors='ignore')
    # fill remaining nulls
    for s in SEVERITY_BUCKETS:
        col = f'severity_{s}'
        if col not in df.columns:
            df[col] = 0
        df[col] = df[col].fillna(0).astype(int)
    df['raw_total'] = df['raw_total'].fillna(0).astype(int)
    # recompute bucket sum to guarantee consistency
    bucket_sum = df[[f'severity_{s}' for s in SEVERITY_BUCKETS]].sum(axis=1)
    df['bucket_sum'] = bucket_sum
    df['num_findings'] = df['num_findings'].fillna(0).astype(int)
    # if num_findings still 0 but raw_total > 0, promote severities (assign to low)
    mask_promote = (df['raw_total'] > 0) & (df['bucket_sum'] == 0)
    if mask_promote.any():
        df.loc[mask_promote, 'severity_low'] = df.loc[mask_promote, 'raw_total']
        df['bucket_sum'] = df[[f'severity_{s}' for s in SEVERITY_BUCKETS]].sum(axis=1)
    # final num_findings = max(existing, raw_total, bucket_sum)
    df['num_findings'] = df[['num_findings', 'raw_total', 'bucket_sum']].max(axis=1).astype(int)
    df['has_findings'] = (df['num_findings'] > 0).astype(int)
    df.drop(columns=['bucket_sum'], inplace=True, errors='ignore')
    return df

def export_anomalies(df: pd.DataFrame, out_dir: str):
    anomalies = df[(df['raw_total'] > 0) & (df['num_findings'] == 0)]
    if not anomalies.empty:
        anomalies.to_csv(os.path.join(out_dir, 'anomalies_rawgt0_num0.csv'), index=False)


def main():
    parser = argparse.ArgumentParser(description='Prepare IaC labels with fallback aggregation.')
    parser.add_argument('--checkov-file', required=True)
    parser.add_argument('--inventory-file', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--debug-positives', action='store_true')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if args.verbose:
        print('Loading inventory...')
    inv = load_inventory(args.inventory_file)
    if args.verbose:
        print(f'Inventory rows: {len(inv):,}')

    if args.verbose:
        print('Loading Checkov findings...')
    chk = load_checkov(args.checkov_file)
    if args.verbose:
        print(f'Checkov findings rows: {len(chk):,}')

    if args.verbose:
        print('Aggregating primary keys...')
    agg_primary = aggregate_checkov(chk)
    if args.verbose:
        print(f'Primary aggregated rows: {len(agg_primary):,}')

    if args.verbose:
        print('Preparing fallback aggregation...')
    # Build a secondary frame keyed on fallback for unmatched resolution
    agg_fb = rekey_for_fallback(agg_primary.merge(chk[['join_key_primary','join_key_fallback']].drop_duplicates(), on='join_key_primary', how='left'))

    if args.verbose:
        print('Merging labels...')
    labels = merge_labels(inv, agg_primary, agg_fb)

    # core output
    out_csv = os.path.join(args.output_dir, 'iac_labels_clean.csv')
    labels_out_cols = ['repo_root','rel_path','abs_path','ext','size_bytes','mtime','raw_total','num_findings','has_findings'] + [f'severity_{s}' for s in SEVERITY_BUCKETS]
    labels[labels_out_cols].to_csv(out_csv, index=False)

    # summary meta
    total_files = len(labels)
    positives = int(labels['has_findings'].sum())
    prevalence = positives / total_files if total_files else 0.0
    summary = pd.DataFrame([
        {'metric':'total_files','value':total_files},
        {'metric':'positives','value':positives},
        {'metric':'prevalence','value':prevalence},
    ])
    summary.to_csv(os.path.join(args.output_dir, 'iac_labels_summary.csv'), index=False)

    export_anomalies(labels, args.output_dir)

    if args.debug_positives:
        pos_sample = labels[labels['has_findings']==1].head(50)
        pos_sample.to_csv(os.path.join(args.output_dir, 'debug_positive_examples.csv'), index=False)

    if args.verbose:
        print(f'Total files: {total_files:,}')
        print(f'Positive files: {positives:,} (prevalence {prevalence:.4%})')
        anomalies_path = os.path.join(args.output_dir, 'anomalies_rawgt0_num0.csv')
        if os.path.exists(anomalies_path):
            print('Anomalies detected -> anomalies_rawgt0_num0.csv')
        else:
            print('No anomalies (raw_total>0 with num_findings==0).')

if __name__ == '__main__':
    main()

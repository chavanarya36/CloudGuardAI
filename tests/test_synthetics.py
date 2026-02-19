import pytest
from pathlib import Path
import zipfile

try:
    from scripts.zip_synthetic import create_zip_from_dir, list_files
except ImportError:
    pytest.skip("scripts.zip_synthetic not available", allow_module_level=True)


def test_create_zip_from_dir_roundtrip(tmp_path: Path) -> None:
    base = tmp_path / "synthetic"
    base.mkdir()
    (base / "a.txt").write_text("alpha", encoding="utf-8")
    (base / "sub").mkdir()
    (base / "sub" / "b.txt").write_text("bravo", encoding="utf-8")

    out_zip = tmp_path / "synthetic_samples.zip"

    create_zip_from_dir(base, out_zip)

    assert out_zip.exists()
    with zipfile.ZipFile(out_zip, "r") as zf:
        names = set(zf.namelist())
        assert "a.txt" in names
        assert "sub/b.txt" in names


def test_list_files_returns_correct_paths(tmp_path: Path) -> None:
    base = tmp_path / "synthetic"
    base.mkdir()
    files = [
        base / "a.txt",
        base / "b.tf",
        base / "sub" / "c.yaml",
    ]
    for f in files:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("x", encoding="utf-8")

    returned = list(list_files(base))
    returned_rel = {p.relative_to(base).as_posix() for p in returned}

    assert "a.txt" in returned_rel
    assert "b.tf" in returned_rel
    assert "sub/c.yaml" in returned_rel
    assert len(returned) == len(files)
from utils.prediction_engine import PredictionEngine
from pathlib import Path
import scripts.zip_synthetic as zs


def main():
    # Ensure synthetic zip exists (create if missing)
    zip_path = Path('synthetic_samples.zip')
    if not zip_path.exists():
        print('Creating synthetic_samples.zip...')
        zs
    
    # If the script produced the zip, scripts.zip_synthetic writes to repo root
    if not zip_path.exists():
        print('Running zip script...')
        try:
            import runpy
            runpy.run_path('scripts/zip_synthetic.py', run_name='__main__')
        except Exception as e:
            print('Failed to create zip:', e)
            return

    print('Loading prediction engine...')
    engine = PredictionEngine()
    print('Processing synthetic_samples.zip...')
    results = engine.process_zip_file(str(zip_path))

    if not results:
        print('No IaC files found in the zip or processing returned empty results')
        return

    # Print concise table
    print('\nResults:')
    print('{:<40} {:>8} {:>12} {:>10} {}'.format('File', 'Prob(%)', 'Band', 'FinalLabel', 'HeuristicReasons'))
    for r in results:
        print('{:<40} {:>8.2f} {:>12} {:>10} {}'.format(
            r['filename'][:40], r['risk_percentage'], r.get('risk_band',''), r.get('final_label',''), ','.join(r.get('heuristic_reasons', []))
        ))

if __name__ == '__main__':
    main()

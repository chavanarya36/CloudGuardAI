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

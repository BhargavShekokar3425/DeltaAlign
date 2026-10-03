"""Run paired historical/corrected normalization without retuning policies."""
import argparse
from experiments.e03_repair_quality import run
from src.normalization import initial_scale


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['legacy', 'corrected'], required=True)
    args = parser.parse_args()
    run(config_path='configs/e04_normalization.json', output_stem=f'e04_{args.mode}',
        scale_function=initial_scale if args.mode == 'corrected' else None,
        normalization='unit_constant' if args.mode == 'corrected' else 'legacy_epsilon',
        verify_e02_replay=False)

#!/usr/bin/env python3
"""Local readiness CLI — computes rolling HRV baseline and readiness from local session files.

Usage:
  python tools/local_readiness.py --hrv 42 --rhr 57 --rhr7 53 --sleep 8 --energy 6 --symptoms 1

Prints JSON with `hrv_baseline` and `readiness` output.
"""
import argparse
import json
import os
import datetime
import importlib.util


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--hrv", type=float, required=True)
    p.add_argument("--rhr", type=int, required=True)
    p.add_argument("--rhr7", type=int, default=None)
    p.add_argument("--sleep", type=float, required=True)
    p.add_argument("--energy", type=int, default=None)
    p.add_argument("--symptoms", type=int, default=0)
    args = p.parse_args()

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readiness_path = os.path.join(repo_root, 'azure-functions', 'shared', 'readiness.py')
    readiness = load_module(readiness_path, 'readiness')

    today = datetime.date.today()
    sessions_dir = os.path.join(repo_root, 'data', 'sessions')

    hrv_baseline = readiness.compute_hrv_baseline(sessions_dir, today)

    snapshot = {
        'hrv_ms': args.hrv,
        'rhr_bpm': args.rhr,
        'rhr_7day_avg': args.rhr7 or args.rhr,
        'sleep_hours': args.sleep,
        'energy': args.energy,
        'symptom_load': args.symptoms,
    }

    readiness_result = readiness.compute_readiness(snapshot, previous_session_flags=None, hrv_baseline=hrv_baseline)

    out = {
        'date': today.isoformat(),
        'hrv_baseline': hrv_baseline,
        'snapshot': snapshot,
        'readiness': readiness_result,
    }

    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()

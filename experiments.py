"""Repeatable experiments for the indoor Monte Carlo Localization simulation.

Examples:
    python experiments.py --seeds 1 2 3 --steps 100 --output outputs/experiments.csv
    python experiments.py --seeds 1 2 3 --steps 100 --particle-counts 50 100 200

The script records observed results; it does not hard-code expected performance.
"""
import argparse
import csv
import os
import time
import numpy as np

from main import IndoorMap, Robot, MCL, control


def run_trial(seed, steps, particle_count):
    """Run one trial and return measured error/runtime statistics."""
    rng = np.random.default_rng(seed)
    world = IndoorMap()
    robot = Robot(world, rng)
    mcl = MCL(
        world,
        particle_count,
        np.random.default_rng(seed + 1_000_003),
        robot.beams,
        robot.max_range,
    )
    errors = []
    start = time.perf_counter()
    for step in range(steps):
        v, omega = control(step)
        odometry = robot.move(v, omega)
        observation = robot.sense()
        estimate = mcl.step(odometry, observation)
        errors.append(float(np.linalg.norm(estimate[:2] - robot.pose[:2])))
    elapsed = time.perf_counter() - start
    values = np.asarray(errors, dtype=float)
    return {
        "seed": seed,
        "steps": steps,
        "particles": particle_count,
        "mean_position_error_m": float(values.mean()),
        "median_position_error_m": float(np.median(values)),
        "final_position_error_m": float(values[-1]),
        "p95_position_error_m": float(np.percentile(values, 95)),
        "runtime_seconds": float(elapsed),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--seeds", type=int, nargs="+", default=[11, 22, 33])
    parser.add_argument("--particle-counts", type=int, nargs="+", default=[50, 100, 200])
    parser.add_argument("--output", default="outputs/experiments.csv")
    args = parser.parse_args()

    if args.steps < 1:
        parser.error("--steps must be at least 1")
    if not args.seeds:
        parser.error("provide at least one seed")
    if any(n < 2 for n in args.particle_counts):
        parser.error("each particle count must be at least 2")

    rows = []
    for count in args.particle_counts:
        for seed in args.seeds:
            row = run_trial(seed, args.steps, count)
            rows.append(row)
            print(
                f"particles={count:4d} seed={seed:4d} "
                f"mean_error={row['mean_position_error_m']:.4f} m "
                f"final_error={row['final_position_error_m']:.4f} m "
                f"runtime={row['runtime_seconds']:.2f} s"
            )

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(args.output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} trial records to {args.output}")


if __name__ == "__main__":
    main()

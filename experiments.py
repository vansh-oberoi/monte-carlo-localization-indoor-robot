"""Repeatable experiments for the indoor Monte Carlo Localization simulation.

Examples:
    python experiments.py --seeds 1 2 3 --steps 100 --output outputs/experiments.csv
    python experiments.py --methods systematic multinomial stratified --seeds 11 22 33
    python experiments.py --scenario kidnap --methods systematic augmented --steps 120
    python experiments.py --lidar-sigmas 0.035 0.1 0.2 --odom-scales 1 2 4

The script records observed results; it does not hard-code expected performance.
"""
import argparse
import csv
import os
import time
import numpy as np

from main import IndoorMap, Robot, MCL, control

METHODS = {
    "systematic":     dict(resampler="systematic",  ess_ratio=None, augmented=False),
    "multinomial":    dict(resampler="multinomial", ess_ratio=None, augmented=False),
    "stratified":     dict(resampler="stratified",  ess_ratio=None, augmented=False),
    "systematic_ess": dict(resampler="systematic",  ess_ratio=0.5,  augmented=False),
    "augmented":      dict(resampler="systematic",  ess_ratio=None, augmented=True),
}


def recovery_steps(errors, ref, threshold=0.5, hold=5):
    """Return steps to sustained recovery, or NaN if recovery never occurs."""
    if not isinstance(ref, (int, np.integer)) or isinstance(ref, (bool, np.bool_)) or ref < 0:
        raise ValueError("ref must be a non-negative integer")
    if not isinstance(hold, (int, np.integer)) or isinstance(hold, (bool, np.bool_)) or hold <= 0:
        raise ValueError("hold must be a positive integer")

    errors = np.asarray(errors)
    if errors.ndim != 1:
        raise ValueError("errors must be a one-dimensional array")
    if ref >= len(errors):
        return float("nan")

    below = errors[ref:] < threshold
    for i in range(len(below) - hold + 1):
        if below[i:i + hold].all():
            return float(i)
    return float("nan")


def run_trial(seed, steps, particle_count, method="systematic", scenario="tracking",
              kidnap_step=50, lidar_sigma=0.035, odom_scale=1.0):
    """Run one trial and return measured error/runtime statistics."""
    rng = np.random.default_rng(seed)
    world = IndoorMap()
    robot = Robot(world, rng)
    robot.lidar_sigma, robot.odom_noise_scale = lidar_sigma, odom_scale
    mcl = MCL(
        world,
        particle_count,
        np.random.default_rng(seed + 1_000_003),
        robot.beams,
        robot.max_range,
        global_init=(scenario == "global"),
        **METHODS[method],
    )
    errors = []
    start = time.perf_counter()

    for step in range(steps):
        initial_scan = robot.sense()
        v, omega = control(step, initial_scan, robot.beams)
        odometry = robot.move(v, omega)
        if scenario == "kidnap" and step == kidnap_step:
            robot.kidnap()
        observation = robot.sense()
        estimate = mcl.step(odometry, observation)
        errors.append(float(np.linalg.norm(estimate[:2] - robot.pose[:2])))

    elapsed = time.perf_counter() - start
    values = np.asarray(errors)
    ref = {"kidnap": kidnap_step, "global": 0}.get(scenario)

    return {
        "scenario": scenario,
        "method": method,
        "seed": seed,
        "steps": steps,
        "particles": particle_count,
        "lidar_sigma": lidar_sigma,
        "odom_scale": odom_scale,
        "mean_position_error_m": float(values.mean()),
        "median_position_error_m": float(np.median(values)),
        "final_position_error_m": float(values[-1]),
        "p95_position_error_m": float(np.percentile(values, 95)),
        "recovery_steps": recovery_steps(values, ref) if ref is not None else float("nan"),
        "runtime_seconds": float(elapsed),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--seeds", type=int, nargs="+", default=[11, 22, 33])
    parser.add_argument("--particle-counts", type=int, nargs="+", default=[50, 100, 200])
    parser.add_argument("--output", default="outputs/experiments.csv")
    parser.add_argument("--methods", nargs="+", default=["systematic"], choices=list(METHODS))
    parser.add_argument("--scenario", choices=["tracking", "global", "kidnap"], default="tracking")
    parser.add_argument("--kidnap-step", type=int, default=50)
    parser.add_argument("--lidar-sigmas", type=float, nargs="+", default=[0.035])
    parser.add_argument("--odom-scales", type=float, nargs="+", default=[1.0])
    args = parser.parse_args()

    if args.steps < 1:
        parser.error("--steps must be at least 1")
    if not args.seeds:
        parser.error("provide at least one seed")
    if any(n < 2 for n in args.particle_counts):
        parser.error("each particle count must be at least 2")
    if args.scenario == "kidnap" and not (0 <= args.kidnap_step < args.steps - 5):
        parser.error("--kidnap-step must leave at least 5 steps before the end")

    rows = []
    for method in args.methods:
        for count in args.particle_counts:
            for sigma in args.lidar_sigmas:
                for scale in args.odom_scales:
                    for seed in args.seeds:
                        row = run_trial(seed, args.steps, count, method, args.scenario,
                                        args.kidnap_step, sigma, scale)
                        rows.append(row)
                        print(
                            f"{method:14s} n={count:4d} seed={seed:4d} "
                            f"lidar={sigma:.3f} odom_x={scale:.1f} "
                            f"mean_error={row['mean_position_error_m']:.4f} m "
                            f"final_error={row['final_position_error_m']:.4f} m "
                            f"recovery={row['recovery_steps']} "
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
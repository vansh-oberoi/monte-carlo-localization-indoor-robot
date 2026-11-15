#!/usr/bin/env python3
"""Reproduce report Figures 5 and 6 from deterministic E1 tracking runs.

Uses the same robot/filter construction and RNG streams as experiments.run_trial:
robot seed = seed; particle-filter seed = seed + 1_000_003.
Outputs per-step CSV traces and two report figures under outputs/.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from main import IndoorMap, Robot, MCL, control, wrap_angle, WAYPOINTS
from experiments import METHODS

ROOT = Path(__file__).resolve().parent


def run_trace(seed: int, particles: int, steps: int = 250):
    rng = np.random.default_rng(seed)
    world = IndoorMap()
    robot = Robot(world, rng)
    mcl = MCL(
        world, particles, np.random.default_rng(seed + 1_000_003),
        robot.beams, robot.max_range, **METHODS["systematic"]
    )
    truths, estimates, clouds, pos_errors, heading_errors = [], [], [], [], []
    waypoint_index = 0

    for _ in range(steps):
        initial_scan = robot.sense()
        v, omega, waypoint_index = control(
            robot.pose, initial_scan, robot.beams, waypoint_index
        )
        odometry = robot.move(v, omega)
        observation = robot.sense()
        estimate = mcl.step(odometry, observation)

        truths.append(robot.pose.copy())
        estimates.append(estimate.copy())
        clouds.append(mcl.particles.copy())
        pos_errors.append(float(np.linalg.norm(estimate[:2] - robot.pose[:2])))
        heading_errors.append(float(abs(np.degrees(
            wrap_angle(estimate[2] - robot.pose[2])
        ))))

    return (world, np.asarray(truths), np.asarray(estimates),
            np.asarray(clouds), np.asarray(pos_errors), np.asarray(heading_errors))


def save_trace(path: Path, seed: int, particles: int, truth, estimate,
               pos_error, heading_error):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "seed", "particles", "step", "true_x_m", "true_y_m", "true_theta_rad",
            "estimate_x_m", "estimate_y_m", "estimate_theta_rad",
            "position_error_m", "heading_error_deg"
        ])
        for i in range(len(pos_error)):
            writer.writerow([
                seed, particles, i + 1, *truth[i], *estimate[i],
                pos_error[i], heading_error[i]
            ])


def figure_5(world, truth, estimate, clouds, output: Path):
    steps = (1, 125, 250)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, step in zip(axes, steps):
        idx = step - 1
        world.draw(ax)
        ax.plot(truth[:step, 0], truth[:step, 1], "b-", lw=1.8, label="Ground truth")
        ax.plot(estimate[:step, 0], estimate[:step, 1], "r--", lw=1.6, label="Estimate")
        ax.scatter(clouds[idx][:, 0], clouds[idx][:, 1], s=9, alpha=0.35,
                   label="Particles")
        ax.plot(truth[idx, 0], truth[idx, 1], "bo", ms=5)
        ax.plot(estimate[idx, 0], estimate[idx, 1], "rx", ms=7)
        ax.set_title(f"Step {step}")
        if step == 1:
            ax.legend(fontsize=8, loc="upper right")
    fig.suptitle("Position tracking (seed 11, N = 200)")
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)


def figure_6(position, heading, output: Path):
    steps = np.arange(1, len(next(iter(position.values()))) + 1)
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for seed in sorted(position):
        axes[0].plot(steps, position[seed], alpha=0.45, lw=0.9, label=f"Seed {seed}")
        axes[1].plot(steps, heading[seed], alpha=0.45, lw=0.9, label=f"Seed {seed}")
    pos_stack = np.vstack([position[s] for s in sorted(position)])
    head_stack = np.vstack([heading[s] for s in sorted(heading)])
    axes[0].plot(steps, np.median(pos_stack, axis=0), color="black",
                 lw=2.0, label="Median")
    axes[1].plot(steps, np.median(head_stack, axis=0), color="black",
                 lw=2.0, label="Median")
    axes[0].set_ylabel("Position error (m)")
    axes[1].set_ylabel("Absolute heading error (degrees)")
    axes[1].set_xlabel("Step")
    axes[0].set_title("Tracking errors (N = 100, five seeds)")
    for ax in axes:
        ax.grid(alpha=0.25)
        ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs")
    parser.add_argument("--steps", type=int, default=250)
    args = parser.parse_args()
    if args.steps < 250:
        parser.error("The report figures require at least 250 steps.")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    world, truth, estimate, clouds, pos, heading = run_trace(11, 200, args.steps)
    figure_5(world, truth, estimate, clouds, args.output_dir / "figure5_tracking_snapshots.png")
    save_trace(args.output_dir / "e1_seed11_n200_trace.csv", 11, 200,
               truth, estimate, pos, heading)

    positions, headings = {}, {}
    for seed in (11, 22, 33, 44, 55):
        world, truth, estimate, _, pos, heading = run_trace(seed, 100, args.steps)
        positions[seed], headings[seed] = pos, heading
        save_trace(args.output_dir / f"e1_seed{seed}_n100_trace.csv", seed, 100,
                   truth, estimate, pos, heading)

    figure_6(positions, headings, args.output_dir / "figure6_tracking_errors.png")
    print("Generated Figure 5 and Figure 6 from deterministic E1 traces.")
    print(f"Figure 5: {args.output_dir / 'figure5_tracking_snapshots.png'}")
    print(f"Figure 6: {args.output_dir / 'figure6_tracking_errors.png'}")
    print("E1 traces: seed 11, N=200; seeds 11,22,33,44,55, N=100.")


if __name__ == "__main__":
    main()

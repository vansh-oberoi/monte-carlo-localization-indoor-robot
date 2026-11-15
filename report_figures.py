#!/usr/bin/env python3
"""Build report figures and aggregate tables from the experiment CSVs.

Run from the repository root after generating the nine CSV files listed in
Section 8.5. This script never creates or substitutes experiment observations:
it only summarizes CSV rows that already exist and fails clearly when inputs
are missing or malformed.
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from statistics import mean, median, stdev

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DEFAULT_INPUTS = {
    "e2_particle_count": "outputs/e2_particle_count.csv",
    "e3_resampling": "outputs/e3_resampling.csv",
    "e3b_ess_augmented": "outputs/e3b_ess_augmented.csv",
    "e4_noise": "outputs/e4_noise.csv",
    "e5_global": "outputs/e5_global.csv",
    "e6_kidnap_100": "outputs/e6_kidnap_100.csv",
    "e6_kidnap_300": "outputs/e6_kidnap_300.csv",
    "e7_kidnap_lidar": "outputs/e7_kidnap_lidar.csv",
    "e7_kidnap_odom": "outputs/e7_kidnap_odom.csv",
}
REQUIRED = {
    "seed", "steps", "particles", "mean_position_error_m",
    "median_position_error_m", "final_position_error_m",
    "p95_position_error_m", "mean_heading_error_deg",
    "runtime_seconds",
}
NUMERIC = REQUIRED - {"seed"}


def load_csv(path: Path, label: str) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing {label}: {path}\n"
            "Generate it with the matching command in Section 8.5 before "
            "running report_figures.py. No values are inferred or fabricated."
        )
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = sorted(REQUIRED - fields)
        if missing:
            raise ValueError(
                f"{path} is missing required columns: {', '.join(missing)}. "
                "This may be an older experiment CSV; do not mix it with "
                "the 250-step report experiments."
            )
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path} contains a header but no experiment rows.")
    for line, row in enumerate(rows, start=2):
        for column in NUMERIC:
            try:
                value = float(row[column])
            except (TypeError, ValueError):
                raise ValueError(f"{path}:{line}: invalid {column}={row[column]!r}")
            if not math.isfinite(value):
                # Recovery metrics may legitimately be NaN; core metrics may not.
                if column != "runtime_seconds" and column not in {
                    "mean_position_error_m", "median_position_error_m",
                    "final_position_error_m", "p95_position_error_m",
                    "mean_heading_error_deg",
                }:
                    continue
                raise ValueError(f"{path}:{line}: non-finite {column}")
    return rows


def group_rows(rows: list[dict], keys: tuple[str, ...]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        key = tuple(row.get(k, "") for k in keys)
        groups.setdefault(key, []).append(row)
    summaries = []
    metrics = (
        "mean_position_error_m", "median_position_error_m",
        "final_position_error_m", "p95_position_error_m",
        "mean_heading_error_deg", "runtime_seconds",
    )
    for key, group in sorted(groups.items(), key=lambda item: tuple(str(x) for x in item[0])):
        result = dict(zip(keys, key))
        result["trials"] = len(group)
        for metric in metrics:
            vals = [float(r[metric]) for r in group]
            result[f"{metric}_mean"] = mean(vals)
            result[f"{metric}_sd"] = stdev(vals) if len(vals) > 1 else 0.0
            result[f"{metric}_median"] = median(vals)
        for metric in ("recovery_steps", "sustained_recovery_steps", "heading_recovery_steps"):
            vals = [
                float(r[metric]) for r in group
                if r.get(metric, "") not in ("", "nan", "NaN", "None")
                and math.isfinite(float(r[metric]))
            ]
            result[f"{metric}_successes"] = len(vals)
            result[f"{metric}_mean_success_only"] = mean(vals) if vals else ""
        summaries.append(result)
    return summaries


def write_summary(path: Path, rows: list[dict], keys: tuple[str, ...]) -> None:
    summary = group_rows(rows, keys)
    if not summary:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)


def plot_metric(rows: list[dict], x_key: str, group_key: str | None,
                output: Path, title: str, x_label: str, y_label: str,
                metric: str = "mean_position_error_m") -> None:
    groups: dict[str, dict[str, list[float]]] = {}
    for row in rows:
        series = str(row.get(group_key, "all")) if group_key else "all"
        x = str(row[x_key])
        groups.setdefault(series, {}).setdefault(x, []).append(float(row[metric]))
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for series, points in sorted(groups.items()):
        labels = sorted(points, key=lambda value: float(value) if _is_number(value) else value)
        ys = [mean(points[label]) for label in labels]
        errors = [stdev(points[label]) if len(points[label]) > 1 else 0.0 for label in labels]
        xs = list(range(len(labels)))
        ax.errorbar(xs, ys, yerr=errors, marker="o", capsize=4, label=series)
        ax.set_xticks(xs, labels)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(True, alpha=0.25)
    if group_key and len(groups) > 1:
        ax.legend(title=group_key)
    fig.tight_layout()
    fig.savefig(output, dpi=220)
    plt.close(fig)


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="repository root (default: directory containing this script)")
    parser.add_argument("--allow-missing", action="store_true",
                        help="process available CSVs and report missing ones; never invent data")
    args = parser.parse_args()
    root = args.root.resolve()
    out = root / "outputs"
    out.mkdir(parents=True, exist_ok=True)

    loaded: dict[str, list[dict]] = {}
    missing = []
    for label, relative in DEFAULT_INPUTS.items():
        path = root / relative
        try:
            loaded[label] = load_csv(path, label)
            print(f"[OK] {relative}: {len(loaded[label])} trial rows")
        except FileNotFoundError as exc:
            missing.append(label)
            print(f"[MISSING] {exc}")

    if missing and not args.allow_missing:
        print("\nNo report figures or aggregate tables were generated.")
        print("Generate all nine source CSVs, then rerun this script.")
        return 2
    if not loaded:
        print("No usable experiment CSVs found.")
        return 2

    for label, rows in loaded.items():
        if label == "e2_particle_count":
            keys = ("particles",)
        elif label in ("e3_resampling", "e3b_ess_augmented"):
            keys = ("method", "particles")
        elif label == "e4_noise":
            keys = ("lidar_sigma", "odom_scale")
        elif label == "e5_global":
            keys = ("particles",)
        elif label.startswith("e6_"):
            keys = ("method", "particles")
        elif label == "e7_kidnap_lidar":
            keys = ("method", "lidar_sigma")
        else:
            keys = ("method", "odom_scale")
        write_summary(out / f"{label}_summary.csv", rows, keys)

    plot_specs = {
        "e2_particle_count": ("particles", None, "Particle count vs. tracking error",
                              "Particles", "Mean position error (m)"),
        "e3_resampling": ("particles", "method", "Resampling comparison",
                          "Particles", "Mean position error (m)"),
        "e3b_ess_augmented": ("particles", "method", "ESS and augmented MCL comparison",
                              "Particles", "Mean position error (m)"),
        "e4_noise": ("odom_scale", "lidar_sigma", "Tracking error under sensor noise",
                     "Odometry noise scale", "Mean position error (m)"),
        "e5_global": ("particles", None, "Global localisation vs. particle count",
                      "Particles", "Mean position error (m)"),
        "e6_kidnap_100": ("seed", "method", "Kidnapped robot recovery (100 particles)",
                          "Seed", "Mean position error (m)"),
        "e6_kidnap_300": ("seed", "method", "Kidnapped robot recovery (300 particles)",
                          "Seed", "Mean position error (m)"),
        "e7_kidnap_lidar": ("lidar_sigma", "method", "Kidnapping under LiDAR noise",
                            "LiDAR sigma (m)", "Mean position error (m)"),
        "e7_kidnap_odom": ("odom_scale", "method", "Kidnapping under odometry noise",
                           "Odometry noise scale", "Mean position error (m)"),
    }
    for label, rows in loaded.items():
        x, group, title, xlabel, ylabel = plot_specs[label]
        plot_metric(rows, x, group, out / f"{label}.png", title, xlabel, ylabel)

    print("\nGenerated summaries and figures only from the CSVs listed above.")
    if missing:
        print("Still missing: " + ", ".join(missing))
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())

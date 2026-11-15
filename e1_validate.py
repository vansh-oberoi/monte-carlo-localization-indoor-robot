import os
import zipfile

import numpy as np
import pandas as pd


OUTPUT_DIR = "outputs"
SEEDS = [11, 22, 33, 44, 55]

EXPECTED = {
    "mean_position_error_m": 0.204,
    "median_position_error_m": 0.166,
    "p95_position_error_m": 0.402,
    "mean_heading_error_deg": 3.6,
}


def main():
    run_metrics = []

    for seed in SEEDS:
        filename = f"e1_seed{seed}_n100_trace.csv"
        path = os.path.join(OUTPUT_DIR, filename)

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Missing {path}. Run e1_report_figures.py first."
            )

        df = pd.read_csv(path)
        required = {"position_error_m", "heading_error_deg"}
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(f"{filename} is missing columns: {sorted(missing)}")

        position = df["position_error_m"].dropna().to_numpy()
        heading = df["heading_error_deg"].dropna().to_numpy()

        if len(position) == 0 or len(heading) == 0:
            raise ValueError(f"{filename} contains empty error series.")

        run_metrics.append({
            "seed": seed,
            "mean_position_error_m": float(np.mean(position)),
            "median_position_error_m": float(np.median(position)),
            "p95_position_error_m": float(np.percentile(position, 95)),
            "mean_heading_error_deg": float(np.mean(heading)),
        })

    runs = pd.DataFrame(run_metrics)

    # Report aggregation: calculate each run's metrics first, then aggregate.
    aggregate = {
        "mean_position_error_m": runs["mean_position_error_m"].mean(),
        "median_position_error_m": runs["mean_position_error_m"].median(),
        "p95_position_error_m": runs["p95_position_error_m"].mean(),
        "mean_heading_error_deg": runs["mean_heading_error_deg"].mean(),
    }

    comparison_rows = []
    for metric, expected in EXPECTED.items():
        precision = 1 if metric == "mean_heading_error_deg" else 3
        actual = aggregate[metric]
        comparison_rows.append({
            "metric": metric,
            "report": expected,
            "recomputed": actual,
            "difference": actual - expected,
            "matches_rounded": round(actual, precision) == round(expected, precision),
        })

    comparison = pd.DataFrame(comparison_rows)

    print("\nPER-SEED RESULTS")
    print(runs.to_string(index=False))

    print("\nREPORT AGGREGATION")
    for metric, value in aggregate.items():
        print(f"{metric}: {value:.6f}")

    print("\nREPORT COMPARISON")
    print(comparison.to_string(index=False))

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    runs.to_csv(os.path.join(OUTPUT_DIR, "e1_per_seed_metrics.csv"), index=False)
    comparison.to_csv(
        os.path.join(OUTPUT_DIR, "e1_report_comparison.csv"), index=False
    )

    files = [
        os.path.join(OUTPUT_DIR, "figure5_tracking_snapshots.png"),
        os.path.join(OUTPUT_DIR, "figure6_tracking_errors.png"),
        os.path.join(OUTPUT_DIR, "e1_seed11_n200_trace.csv"),
        *[
            os.path.join(OUTPUT_DIR, f"e1_seed{seed}_n100_trace.csv")
            for seed in SEEDS
        ],
        os.path.join(OUTPUT_DIR, "e1_per_seed_metrics.csv"),
        os.path.join(OUTPUT_DIR, "e1_report_comparison.csv"),
    ]

    missing_files = [path for path in files if not os.path.exists(path)]
    if missing_files:
        raise FileNotFoundError(
            "Cannot create complete validation package; missing files:\n"
            + "\n".join(missing_files)
        )

    package = os.path.join(OUTPUT_DIR, "e1_validation_package.zip")
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=os.path.basename(path))

    print(f"\nValidation package created: {package}")


if __name__ == "__main__":
    main()

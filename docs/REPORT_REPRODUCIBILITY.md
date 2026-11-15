# Report reproducibility pipeline

## What this adds

`report_figures.py` validates the nine experiment CSVs named in Section 8.5,
creates one aggregate summary CSV per experiment, and creates comparison plots.
It reads observed rows only. It does not generate expected values, fill missing
trials, or silently reuse older CSVs.

Run it from the repository root after running the nine experiment commands in
the report:

```bash
python report_figures.py
```

For an incremental check while some experiments are still running:

```bash
python report_figures.py --allow-missing
```

The incremental mode processes only present, schema-compatible inputs and
returns a non-zero exit status while any required input is missing.

## Required inputs

- `outputs/e2_particle_count.csv`
- `outputs/e3_resampling.csv`
- `outputs/e3b_ess_augmented.csv`
- `outputs/e4_noise.csv`
- `outputs/e5_global.csv`
- `outputs/e6_kidnap_100.csv`
- `outputs/e6_kidnap_300.csv`
- `outputs/e7_kidnap_lidar.csv`
- `outputs/e7_kidnap_odom.csv`

The CSVs must contain the metrics emitted by the current `experiments.py`,
including mean heading error and runtime. The generator rejects older CSV
schemas instead of combining results from different experiment protocols.

## Generated artifacts

For each input, the script writes:

- `outputs/<experiment>_summary.csv`: per-setting mean, sample standard
  deviation, median, trial count, and recovery summaries where applicable.
- `outputs/<experiment>.png`: an error-bar comparison plot for E2–E5.
- For E6 and E7, `outputs/<experiment>_recovery.png`: recovery success-rate
  and conditional mean recovery-time plots for initial position, sustained
  position, and heading criteria. The corresponding
  `outputs/<experiment>_position_error.png` retains whole-trial mean position
  error as a complementary diagnostic, not as the recovery measure.

A trial counts as successful for a recovery criterion only when its recorded
recovery step is finite. Mean recovery time is calculated only among trials
that meet that criterion; unsuccessful trials are not assigned a synthetic
recovery time. Success rates use all trials in the relevant setting as the
denominator. The criteria are initial position error below 0.5 m for 5
consecutive samples, sustained position error below 0.5 m for 20 consecutive
samples, and absolute heading error below 15 degrees for 20 consecutive
samples after kidnapping.

These outputs are derived from the corresponding raw trial CSVs. Keep the raw
CSVs alongside the generated summaries when archiving a report run.

## E1 trajectory figures (Figures 5 and 6)

The E1 figures are generated separately because they require per-step states.
Run from the repository root:

```bash
python e1_report_figures.py
```

The script reproduces Figure 5 for seed 11 with 200 particles, including the
particle clouds at steps 1, 125 and 250. It reproduces Figure 6 for five seeds
(11, 22, 33, 44, 55) with 100 particles and plots the per-step position and
absolute heading errors with their across-seed median. It writes the figures
and six per-step trace CSVs under `outputs/`.

The script uses the same deterministic RNG streams as `experiments.run_trial`
(robot seed = seed; particle-filter seed = seed + 1,000,003), and uses the
current `main.py` simulator, controller and filter implementation.

### E1 numerical validation and aggregation

After generating the traces, run the validation script:

```bash
python e1_validate.py
```

It checks the five N=100 traces (seeds 11, 22, 33, 44, 55) against the E1
values reported in the report and creates `outputs/e1_validation_package.zip`.
The package contains Figure 5, Figure 6, all six E1 traces (including seed 11,
N=200), per-seed metrics and the report comparison table.

The report's displayed E1 statistics are reproduced by first calculating
statistics independently for each of the five N=100 runs, then aggregating
those run-level values as follows:

- Mean position error: arithmetic mean of the five per-run mean position errors.
- Median position error: median of the five per-run mean position errors.
- P95 position error: arithmetic mean of the five per-run 95th-percentile position errors.
- Mean heading error: arithmetic mean of the five per-run mean heading errors.

The validated values from the regenerated traces are 0.204348 m (mean
position error), 0.165737 m (median of per-run mean position errors), 0.401643 m
(mean per-run P95 position error), and 3.607554 degrees (mean heading error).
These round to the report's displayed values: 0.204 m, 0.166 m, 0.402 m and
3.6 degrees, respectively.

These are run-level aggregate definitions; they are not the same as pooling
all 1,250 time-step observations and calculating a single median or P95.
Preserve this distinction when reporting or interpreting the metrics. The
validation establishes consistency for the regenerated traces and current
code; it does not by itself prove that any historical figure or trace was
generated with the same code and random-number streams.

## Reproduction record

Record the Git commit, Python version, NumPy/Matplotlib versions, operating
system, CPU and RAM with each final run. Runtime values are machine-dependent.
Do not copy runtime measurements from an earlier machine into a new report.

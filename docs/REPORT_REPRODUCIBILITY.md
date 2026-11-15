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
- `outputs/<experiment>.png`: an error-bar comparison plot.

These outputs are derived from the corresponding raw trial CSVs. Keep the raw
CSVs alongside the generated summaries when archiving a report run.

## E1 trajectory figures (Figures 5 and 6)

The E1 figures are generated separately because they require per-step states
rather than per-trial aggregates. Run from the repository root:

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
current `main.py` simulator, controller and filter implementation. These
figures should be checked against the report after regeneration; do not treat
visual similarity alone as proof that older, separately generated figures
used the same RNG stream.

## Reproduction record

Record the Git commit, Python version, NumPy/Matplotlib versions, operating
system, CPU and RAM with each final run. Runtime values are machine-dependent.
Do not copy runtime measurements from an earlier machine into a new report.

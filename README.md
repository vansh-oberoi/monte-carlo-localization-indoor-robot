# Monte Carlo Localization of an Indoor Robot

A classroom project implementing Monte Carlo Localization (MCL) for a simulated indoor robot using **Python, NumPy, and Matplotlib**.

## Features

- 2D indoor map with walls and rectangular obstacles
- Simulated robot movement and noisy odometry
- Simulated 2D LiDAR using ray casting
- Particle-filter localization: prediction, measurement weighting, and resampling
- Systematic, multinomial, and stratified resampling, with optional ESS-based resampling
- Augmented MCL with random-particle injection for kidnapped-robot recovery experiments
- Repeatable multi-seed experiments with position-error, recovery, and runtime metrics
- Visualization of the map, particles, true pose, estimated pose, LiDAR rays, and trajectory
- Position-error plot and CSV experiment output

## Requirements

- Python 3.10+
- NumPy
- Matplotlib

## Setup

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
```

## Run the simulation

```bash
python main.py
```

Useful options:

```bash
python main.py --steps 120 --particles 180
python main.py --steps 80 --particles 100 --seed 7
```

Close the animation window after viewing. The program saves plots and a summary in `outputs/`.

Run the basic tests:

```bash
python -m unittest discover -s tests -v
```

## How MCL works

1. **Initialize:** represent possible robot poses as particles.
2. **Predict:** move particles using noisy odometry.
3. **Measure:** predict LiDAR ranges from each particle pose.
4. **Weight:** compare predicted ranges with the simulated scan.
5. **Resample:** favor particles with higher likelihood.
6. **Evaluate:** compare the estimated pose with simulator ground truth.

The pose is `(x, y, theta)`; angle values are in radians.

## Project structure

- `main.py` — simulation and visualization
- `requirements.txt` — Python dependencies
- `experiments.py` — repeatable experiments and CSV metrics
- `tests/test_smoke.py` — basic simulation correctness checks
- `tests/test_resamplers.py` — resampling, augmented MCL, and particle validity tests
- `tests/test_recovery.py` — recovery-metric behavior and input validation tests
- `REPORT_OUTLINE.md` — report-writing guide

## Experiments to report

- Compare different particle counts.
- Increase LiDAR noise and observe localization error.
- Increase odometry noise and observe estimation stability.
- Compare mean and final position error and runtime.

**Important:** report only values produced by your own runs. Performance depends on the map, initialization, sensor model, random seed, and simulation parameters.

## Reproducible experiment comparison

A repeatable experiment runner compares particle counts while holding the map, motion sequence, and noise parameters fixed. It runs each configuration over multiple seeds and writes every trial to CSV.

```bash
python experiments.py --steps 100 --seeds 11 22 33 --particle-counts 50 100 200 --output outputs/experiments.csv
```

Recorded metrics include mean, median, final, and 95th-percentile position error, plus runtime. Read [the experiment protocol](docs/EXPERIMENT_PROTOCOL.md) before running and reporting results. The script does not supply prewritten results; use the CSV produced by your own run.

## Continuous integration

GitHub Actions runs the unit tests on Python 3.10, 3.11, and 3.12 for pushes and pull requests. Check the repository's **Actions** tab for the actual run status.

## Scope and limitations

This is an educational 2D simulation with a known map and simplified motion and LiDAR models. It is not a real-robot navigation stack and does not implement SLAM or ROS integration. Localization may be ambiguous in symmetric environments.

## License

This project is released under the MIT License. See [LICENSE](LICENSE).

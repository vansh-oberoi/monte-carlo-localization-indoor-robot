# Monte Carlo Localization of an Indoor Robot

A classroom project implementing Monte Carlo Localization (MCL) for a simulated indoor robot using **Python, NumPy, and Matplotlib**.

## Features

- 2D indoor map with walls and rectangular obstacles
- Simulated robot movement and noisy odometry
- Simulated 2D LiDAR using ray casting
- Particle-filter localization: prediction, measurement weighting, and resampling
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
python -m unittest
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
- `tests/test_smoke.py` — basic correctness checks
- `REPORT_OUTLINE.md` — report-writing guide

## Experiments to report

- Compare different particle counts.
- Increase LiDAR noise and observe localization error.
- Increase odometry noise and observe estimation stability.
- Compare mean and final position error and runtime.

**Important:** report only values produced by your own runs. Performance depends on the map, initialization, sensor model, random seed, and simulation parameters.

## Scope and limitations

This is an educational 2D simulation with a known map and simplified motion and LiDAR models. It is not a real-robot navigation stack and does not implement SLAM or ROS integration. Localization may be ambiguous in symmetric environments.

## License

This project is released under the MIT License. See [LICENSE](LICENSE).

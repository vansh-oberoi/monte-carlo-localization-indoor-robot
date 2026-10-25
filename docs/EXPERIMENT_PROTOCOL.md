# Reproducible Experiment Protocol

## Research question
How does particle count affect localization accuracy and computational cost in this specific simulated map and motion sequence?

## Independent variable
Particle count: 50, 100, and 200 by default. Change the list with `--particle-counts`.

## Repeats and controls
- Use the same list of random seeds for each particle count.
- Each trial uses a fixed seed for robot/sensor randomness and a separate deterministic seed for the particle filter.
- Keep the map, motion command sequence, LiDAR beam count, and noise parameters fixed.
- Each run is an independent trial; report all seeds and parameter settings.

## Metrics
- Mean, median, final, and 95th-percentile Euclidean position error in metres.
- Runtime in seconds, measured with Python's `time.perf_counter()`.

## Run
```bash
python experiments.py --steps 100 --seeds 11 22 33 --particle-counts 50 100 200 --output outputs/experiments.csv
```

## Analysis guidance
Summarize each particle-count setting across seeds (mean and standard deviation for error and runtime). Plot particle count against mean position error and runtime. Inspect individual runs as well as aggregate statistics; a lower error in one seed is not sufficient evidence of a general improvement.

## Important limitations
This is a simplified educational simulator, not a real robot or validated robotics benchmark. The particle filter's motion and sensor models are approximate. The chosen route and map may favor some particle counts. State these limitations in the report.

**Do not write results into the report until the experiment script has been run and the output CSV has been checked.**

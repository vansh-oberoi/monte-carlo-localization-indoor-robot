# Kidnapped-Robot Experiment Results

## Summary

This report records the multi-seed kidnapped-robot comparison between the standard systematic particle filter and the augmented MCL variant in this repository's 2D simulator.

The augmented method performed substantially better in the tested configuration at both 100 and 300 particles. At 300 particles, it met the defined position and heading recovery criteria in all 15 tested seeds. These are simulation results for the specified map, controller, sensor model, motion model, and seed set; they are not a guarantee of performance in other environments or on a physical robot.

## Experimental setup

- Scenario: kidnapped robot
- Steps per trial: 250
- Kidnapping step: 100
- Random seeds: 11, 22, 33, 44, 55, 66, 77, 88, 99, 111, 222, 333, 444, 555, 666
- Methods: systematic MCL and augmented MCL
- Particle counts: 100 and 300
- LiDAR sigma: 0.035
- Odometry scale: 1.0
- Trials: 15 per method and particle count (60 total)

The same seed list and scenario settings were used for both methods at each particle count.

### Reproduction commands

Run from the repository root with the project dependencies installed:

```bash
python experiments.py --steps 250 --seeds 11 22 33 44 55 66 77 88 99 111 222 333 444 555 666 --particle-counts 100 --methods systematic augmented --scenario kidnap --kidnap-step 100 --output outputs/updated_kidnap_15_seeds_v2.csv

python experiments.py --steps 250 --seeds 11 22 33 44 55 66 77 88 99 111 222 333 444 555 666 --particle-counts 300 --methods systematic augmented --scenario kidnap --kidnap-step 100 --output outputs/updated_kidnap_300_particles.csv
```

Each CSV contains one row per trial, including position and heading error metrics, recovery measurements, and runtime. The generated CSV files are local experiment outputs and are not committed as source data in this report.

## Aggregate results

### Position error

| Particle count | Method | Mean position error | Median position error | Mean final position error | Median final position error |
|---:|---|---:|---:|---:|---:|
| 100 | Systematic MCL | 2.5750 m | — | 3.5541 m | — |
| 100 | Augmented MCL | 1.2697 m | — | 1.7861 m | — |
| 300 | Systematic MCL | 2.6120 m | 2.2267 m | 3.7527 m | 3.9937 m |
| 300 | Augmented MCL | 0.6355 m | 0.4499 m | 0.6539 m | 0.1794 m |

At 300 particles, augmented MCL reduced mean position error by approximately 75.7% and mean final position error by approximately 82.6% relative to systematic MCL in this experiment.

The 100-particle means are summarized from the recorded 15-seed experiment. The median values were not retained in the experiment summary used to prepare this report, so they are intentionally not stated here.

### Recovery criteria and results

The experiment code defines:
- **Initial position recovery:** position error below 0.5 m for 5 consecutive samples after the kidnapping step.
- **Sustained position recovery:** position error below 0.5 m for 20 consecutive samples after the kidnapping step.
- **Heading recovery:** absolute heading error below 15 degrees for 20 consecutive samples after the kidnapping step.

| Particle count | Method | Initial position recovery | Sustained position recovery | Heading recovery |
|---:|---|---:|---:|---:|
| 100 | Systematic MCL | 0/15 | 0/15 | 4/15 |
| 100 | Augmented MCL | 11/15 | 11/15 | 12/15 |
| 300 | Systematic MCL | 0/15 | 0/15 | 3/15 |
| 300 | Augmented MCL | 15/15 | 15/15 | 15/15 |

At 300 particles, augmented MCL's mean sustained position recovery time was 35.6 steps (median 29 steps). Mean heading recovery time was 17.2 steps (median 10 steps).

Among the 15 augmented 300-particle trials, the mean post-sustained-recovery position error was 0.512 m (median 0.262 m). Mean post-heading-recovery heading error was 9.557 degrees (median 3.464 degrees). These post-recovery averages are conditional on the corresponding recovery criterion being met.

## Interpretation

The results support the conclusion that, under this simulator configuration, augmented MCL is more resilient to the tested kidnapping event than the standard systematic MCL baseline. Increasing the particle count from 100 to 300 coincided with improved recovery rates and lower aggregate errors for augmented MCL.

This comparison does not isolate particle count as the sole cause of improvement across all possible configurations, nor does it establish statistical significance or generalization beyond the tested seeds and scenario. The relatively high final errors in augmented 300-particle seeds 77 (5.8394 m) and 444 (1.7551 m) also show that an earlier recovery event does not guarantee low error at the end of every run.

## Limitations

- This is a simplified 2D educational simulation with a known map and simulated LiDAR/odometry.
- Only one kidnapping scenario configuration and 15 seeds per method/particle count are reported.
- The map, patrol route, controller, sensor model, and motion model affect the results.
- Runtime depends on the machine and execution environment; no cross-machine runtime claim is made.
- Results should not be interpreted as evidence of real-world robot performance.

## Validation

The repository's local test suite was reported by the project author as passing 24 tests. GitHub Actions for the implementation commit also completed successfully. Re-run the tests and experiment commands when reproducing the results in a fresh environment.

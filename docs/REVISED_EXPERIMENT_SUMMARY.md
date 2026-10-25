# Revised experiment summary

## Run configuration

- 100 simulation steps per trial
- Particle counts: 50, 100, 200
- Seeds: 11, 22, 33, 44, 55
- 15 trials total
- Source data: `outputs/experiments_revised.csv`

## Aggregate results

| Metric | 50 particles | 100 particles | 200 particles |
|---|---:|---:|---:|
| Mean of per-trial mean position error (m) | 0.041324 | 0.042157 | 0.039454 |
| Mean final position error (m) | 0.030190 | 0.037750 | 0.034646 |
| Mean of per-trial p95 position error (m) | 0.088614 | 0.087028 | 0.077354 |
| Mean runtime per trial (s) | 0.217284 | 0.429340 | 0.868988 |

## Interpretation

In this run, 200 particles had the lowest average of per-trial mean position error and the lowest average of per-trial 95th-percentile error. 50 particles had the lowest average final position error. The per-trial mean-error averages do not improve monotonically from 50 to 100 to 200 particles. Runtime rose as particle count increased.

These results are descriptive results from five seeds on one simulated map. They do not establish statistical significance, performance on other maps, global localization ability, or real-robot performance. Runtime is dependent on the machine and environment.

## Comparison caveat

The baseline and revised experiments used the same seed list and step count in their extended runs, but changed the invalid-particle handling. Compare their metrics descriptively; do not treat this single implementation change as evidence of a general causal performance improvement. A more rigorous assessment would run more seeds and test varied maps and motion paths.

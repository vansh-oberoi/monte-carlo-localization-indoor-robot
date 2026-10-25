# Preliminary experiment record

These CSV files preserve measurements collected on the initial implementation before invalid-particle relocation was changed:

- [Initial 40-step trials](../outputs/experiments_baseline.csv)
- [Extended 100-step trials](../outputs/experiments_extended.csv)

## Experimental design

- Map: the fixed 10 m × 10 m simulated indoor map defined in `main.py`
- Robot motion: deterministic control schedule with seeded robot motion/sensor noise
- Particle counts: 50, 100, 200 in the extended comparison
- Seeds: 11, 22, 33, 44, 55 in the extended comparison
- Trials: 100 steps per trial in the extended comparison
- Metrics: mean, median, final and 95th-percentile position error; runtime

## Important limitation

These are preliminary baseline results from the original implementation, which relocated invalid particles to random valid map positions. The implementation now rejects invalid motion proposals and retains a particle's previous valid pose if ten proposals fail. Therefore, do not combine these baseline results with results from the revised implementation. Rerun the same experiment command after pulling the updated code, and save the new output under a different filename.

Runtime is machine-dependent. The experiments use one simulated map and local initialization around a known starting pose; they do not establish global localization performance or real-robot performance.

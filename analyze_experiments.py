import csv
import os
import numpy as np
import matplotlib.pyplot as plt

path = "outputs/experiments_revised.csv"
rows = []

with open(path, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        rows.append(row)

particle_counts = sorted(set(int(r["particles"]) for r in rows))
means = []
stds = []
runtimes = []

for count in particle_counts:
    group = [r for r in rows if int(r["particles"]) == count]
    errors = np.array(
        [float(r["mean_position_error_m"]) for r in group]
    )
    times = np.array([float(r["runtime_seconds"]) for r in group])

    means.append(errors.mean())
    stds.append(errors.std(ddof=1))
    runtimes.append(times.mean())

    print(
        f"{count:3d} particles | "
        f"mean error = {errors.mean():.5f} m | "
        f"SD = {errors.std(ddof=1):.5f} m | "
        f"mean runtime = {times.mean():.3f} s"
    )

os.makedirs("outputs", exist_ok=True)

plt.figure(figsize=(7, 5))
plt.errorbar(
    particle_counts, means, yerr=stds,
    fmt="o-", capsize=5
)
plt.xlabel("Number of particles")
plt.ylabel("Mean position error (m)")
plt.title("MCL Accuracy vs. Particle Count")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("outputs/particle_count_comparison.png", dpi=200)
plt.close()

print("\nSaved outputs/particle_count_comparison.png")

#!/usr/bin/env bash
# Run the exact E2-E7 experiment matrix specified in report Section 8.5.
# Execute from the repository root. Raw CSVs are written to outputs/.
set -euo pipefail

python -m pip install -r requirements.txt
python -m unittest discover -s tests

S=(--steps 250 --seeds 11 22 33 44 55)
G=(--steps 250 --seeds 11 22 33 44 55 66 77 88 99 111)
K=(--steps 250 --scenario kidnap --kidnap-step 100
   --methods systematic augmented
   --seeds 11 22 33 44 55 66 77 88 99 111 222 333 444 555 666)

mkdir -p outputs

python experiments.py "${S[@]}" --methods systematic \
  --particle-counts 25 50 100 200 400 800 --output outputs/e2_particle_count.csv

python experiments.py "${S[@]}" --particle-counts 50 100 200 \
  --methods multinomial stratified systematic --output outputs/e3_resampling.csv

python experiments.py "${S[@]}" --particle-counts 100 200 \
  --methods systematic systematic_ess augmented --output outputs/e3b_ess_augmented.csv

python experiments.py "${S[@]}" --particle-counts 100 --methods systematic \
  --lidar-sigmas 0.035 0.1 0.2 --odom-scales 1 2 4 --output outputs/e4_noise.csv

python experiments.py "${G[@]}" --scenario global --particle-counts 200 1000 \
  --methods systematic --output outputs/e5_global.csv

python experiments.py "${K[@]}" --particle-counts 100 --output outputs/e6_kidnap_100.csv

python experiments.py "${K[@]}" --particle-counts 300 --output outputs/e6_kidnap_300.csv

python experiments.py "${K[@]}" --particle-counts 100 --lidar-sigmas 0.02 0.035 0.07 \
  --output outputs/e7_kidnap_lidar.csv

python experiments.py "${K[@]}" --particle-counts 100 --odom-scales 1 2 4 \
  --output outputs/e7_kidnap_odom.csv

python report_figures.py

echo "All report experiments and report figure generation completed."

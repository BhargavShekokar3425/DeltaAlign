# Candidate-dependency and closure findings

Completed 1200 detector observations (120 independently reset full-align update trials, reused across K and seed detectors). All incremental cost comparisons and candidate refresh comparisons matched their full references. Old-match feasibility and closure target separation assertions passed.

The study uses 1K BA graphs, fixed 1% observation noise, development seeds 0–4, and holdout seeds 5–9. Candidate top-K lists always include old matches. Both-graph one-edit trials duplicate source-only conditions by budget allocation. Full descriptors and cached dense costs are correctness references; these results do not measure incremental update latency or speedup.

## Sparse-update closure tradeoff

Conservative radius-2 support detection (mean values; recall excludes zero-change trials):

| Split | Update side | Fraction | K | Seed RF | Final RF | Recall | Nonempty |
|---|---|---|---|---|---|---|---|
| development | source | 0.01% | 1 | 12.96% | 13.62% | 77.78% | 3/5 |
| development | source | 0.01% | 2 | 12.96% | 23.76% | 86.11% | 3/5 |
| development | source | 0.01% | 5 | 12.96% | 83.90% | 97.22% | 3/5 |
| development | source | 0.01% | 20 | 12.96% | 91.12% | 97.22% | 3/5 |
| development | source | 0.10% | 1 | 58.70% | 61.96% | 78.68% | 4/5 |
| development | source | 0.10% | 2 | 58.70% | 75.78% | 90.87% | 4/5 |
| development | source | 0.10% | 5 | 58.70% | 94.82% | 96.76% | 4/5 |
| development | source | 0.10% | 20 | 58.70% | 98.30% | 98.79% | 4/5 |
| development | target | 0.01% | 1 | 14.28% | 16.10% | 50.00% | 2/5 |
| development | target | 0.01% | 2 | 20.86% | 34.06% | 50.00% | 2/5 |
| development | target | 0.01% | 5 | 38.56% | 89.78% | 100.00% | 2/5 |
| development | target | 0.01% | 20 | 77.40% | 97.72% | 100.00% | 2/5 |
| development | target | 0.10% | 1 | 64.44% | 68.64% | 83.33% | 3/5 |
| development | target | 0.10% | 2 | 79.44% | 88.84% | 100.00% | 3/5 |
| development | target | 0.10% | 5 | 94.46% | 99.48% | 100.00% | 3/5 |
| development | target | 0.10% | 20 | 99.98% | 100.00% | 100.00% | 3/5 |
| development | both | 0.01% | 1 | 12.96% | 13.62% | 77.78% | 3/5 |
| development | both | 0.01% | 2 | 12.96% | 23.76% | 86.11% | 3/5 |
| development | both | 0.01% | 5 | 12.96% | 83.90% | 97.22% | 3/5 |
| development | both | 0.01% | 20 | 12.96% | 91.12% | 97.22% | 3/5 |
| development | both | 0.10% | 1 | 58.54% | 61.10% | 90.16% | 3/5 |
| development | both | 0.10% | 2 | 67.88% | 80.22% | 98.25% | 3/5 |
| development | both | 0.10% | 5 | 82.40% | 98.12% | 99.12% | 3/5 |
| development | both | 0.10% | 20 | 98.22% | 99.94% | 100.00% | 3/5 |
| holdout | source | 0.01% | 1 | 18.78% | 20.34% | 50.00% | 1/5 |
| holdout | source | 0.01% | 2 | 18.78% | 35.08% | 100.00% | 1/5 |
| holdout | source | 0.01% | 5 | 18.78% | 87.56% | 100.00% | 1/5 |
| holdout | source | 0.01% | 20 | 18.78% | 94.52% | 100.00% | 1/5 |
| holdout | source | 0.10% | 1 | 60.98% | 63.14% | 74.87% | 5/5 |
| holdout | source | 0.10% | 2 | 60.98% | 77.64% | 87.19% | 5/5 |
| holdout | source | 0.10% | 5 | 60.98% | 95.66% | 96.57% | 5/5 |
| holdout | source | 0.10% | 20 | 60.98% | 99.22% | 98.69% | 5/5 |
| holdout | target | 0.01% | 1 | 17.64% | 19.12% | 63.64% | 2/5 |
| holdout | target | 0.01% | 2 | 26.72% | 40.90% | 81.82% | 2/5 |
| holdout | target | 0.01% | 5 | 46.38% | 92.54% | 90.91% | 2/5 |
| holdout | target | 0.01% | 20 | 80.68% | 99.02% | 90.91% | 2/5 |
| holdout | target | 0.10% | 1 | 70.80% | 73.10% | 76.49% | 5/5 |
| holdout | target | 0.10% | 2 | 83.94% | 90.54% | 90.59% | 5/5 |
| holdout | target | 0.10% | 5 | 96.50% | 99.66% | 100.00% | 5/5 |
| holdout | target | 0.10% | 20 | 99.98% | 100.00% | 100.00% | 5/5 |
| holdout | both | 0.01% | 1 | 18.78% | 20.34% | 50.00% | 1/5 |
| holdout | both | 0.01% | 2 | 18.78% | 35.08% | 100.00% | 1/5 |
| holdout | both | 0.01% | 5 | 18.78% | 87.56% | 100.00% | 1/5 |
| holdout | both | 0.01% | 20 | 18.78% | 94.52% | 100.00% | 1/5 |
| holdout | both | 0.10% | 1 | 63.64% | 66.10% | 71.02% | 5/5 |
| holdout | both | 0.10% | 2 | 72.40% | 84.02% | 89.69% | 5/5 |
| holdout | both | 0.10% | 5 | 86.56% | 98.56% | 97.50% | 5/5 |
| holdout | both | 0.10% | 20 | 99.22% | 99.98% | 100.00% | 5/5 |

## Exact changed-feature diagnostic

| Split | Side | Fraction | K | Final RF | Recall |
|---|---|---|---|---|---|
| development | source | 0.01% | 1 | 12.94% | 77.78% |
| development | source | 0.01% | 2 | 22.24% | 86.11% |
| development | source | 0.01% | 5 | 83.86% | 97.22% |
| development | source | 0.10% | 1 | 45.46% | 62.30% |
| development | source | 0.10% | 2 | 62.68% | 77.41% |
| development | source | 0.10% | 5 | 92.72% | 95.19% |
| development | target | 0.01% | 1 | 10.22% | 50.00% |
| development | target | 0.01% | 2 | 23.76% | 50.00% |
| development | target | 0.01% | 5 | 86.44% | 100.00% |
| development | target | 0.10% | 1 | 43.54% | 75.00% |
| development | target | 0.10% | 2 | 71.44% | 87.50% |
| development | target | 0.10% | 5 | 97.26% | 100.00% |
| development | both | 0.01% | 1 | 12.94% | 77.78% |
| development | both | 0.01% | 2 | 22.24% | 86.11% |
| development | both | 0.01% | 5 | 83.86% | 97.22% |
| development | both | 0.10% | 1 | 41.78% | 86.93% |
| development | both | 0.10% | 2 | 63.24% | 96.09% |
| development | both | 0.10% | 5 | 95.34% | 98.70% |
| holdout | source | 0.01% | 1 | 7.44% | 50.00% |
| holdout | source | 0.01% | 2 | 16.02% | 100.00% |
| holdout | source | 0.01% | 5 | 84.94% | 100.00% |
| holdout | source | 0.10% | 1 | 36.92% | 63.32% |
| holdout | source | 0.10% | 2 | 55.72% | 71.15% |
| holdout | source | 0.10% | 5 | 92.16% | 95.25% |
| holdout | target | 0.01% | 1 | 10.20% | 63.64% |
| holdout | target | 0.01% | 2 | 25.24% | 81.82% |
| holdout | target | 0.01% | 5 | 89.52% | 90.91% |
| holdout | target | 0.10% | 1 | 44.20% | 69.30% |
| holdout | target | 0.10% | 2 | 70.86% | 83.55% |
| holdout | target | 0.10% | 5 | 98.14% | 100.00% |
| holdout | both | 0.01% | 1 | 7.44% | 50.00% |
| holdout | both | 0.01% | 2 | 16.02% | 100.00% |
| holdout | both | 0.01% | 5 | 84.94% | 100.00% |
| holdout | both | 0.10% | 1 | 47.46% | 60.51% |
| holdout | both | 0.10% | 2 | 68.76% | 76.53% |
| holdout | both | 0.10% | 5 | 96.56% | 97.50% |

## Interpretation

Exact candidate maintenance is validated, including new target entrants. It does not imply detection equivalence to dense FullAlign: omitted candidate alternatives can carry dense optimum changes. Conversely, adding more alternatives can recursively bring many old owners into closure. The full grouped JSON includes every K, larger update fractions, minimum recall, and maximum RF; inspect seed-level misses before choosing a repair policy.

The next decision should use recall together with final RF, and remain scoped to this topology/noise. Conservative structural support and exact changed-feature seeds are separate detectors; the latter currently requires a full feature oracle and is not a deployable incremental detector. No candidate K should be presented as universally correct based on this diagnostic.

## Decision and next experiment

Do not proceed to large-scale or parallel repair with unconditional top-K ownership closure. It expands the repair set toward the whole graph; lowering K reduces expansion but misses dense full-alignment changes. Exact feature seeds reduce some unnecessary structural expansion without eliminating the candidate-competition problem.

Next evaluate cost-margin candidate pruning and confidence-based seeds as a detection-only ablation. Retain old-match edges, refresh changed-target costs against all sources, and compare the pruned detector with both unpruned closure and fixed-radius detection. Choose margin settings on development seeds and assess them once on a fresh validation split; seeds 5–9 are now observed and should not be reused as untouched validation. If recall still requires near-global RF, record that limitation and reconsider the localization premise before investing in repair. A pruned candidate detector will have empirical recall, not exact equivalence to dense assignment.

The feature-update path is also still an oracle: implementing local descriptor updates remains necessary before any performance claim. These experiments provide correctness and region-growth evidence only.

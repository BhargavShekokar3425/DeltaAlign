# E00 findings

This report is generated from the 1K diagnostic baseline. Results are pipeline-specific; no repair speedup has been measured.

Initial NC mean: 0.683. Random-mapping NC mean: 0.000.

| Requested update | Actual edits | Mean changed fraction | Mean updated NC | Median full solve (s) |
|---|---|---|---|---|
| 0.01% | 1–1 | 0.073 | 0.678 | 0.0583 |
| 0.10% | 6–6 | 0.149 | 0.670 | 0.0576 |
| 1.00% | 60–60 | 0.472 | 0.504 | 0.0731 |
| 5.00% | 299–299 | 0.805 | 0.202 | 0.1376 |

| Update | Radius | Mean RF | Mean recall (nonempty C*) |
|---|---|---|---|
| 0.01% | 0 | 0.002 | 0.037534280040348 |
| 0.01% | 1 | 0.009 | 0.04298027518597907 |
| 0.01% | 2 | 0.130 | 0.23367028905560458 |
| 0.01% | 3 | 0.662 | 0.5450041766485941 |
| 0.10% | 0 | 0.012 | 0.05501414533275472 |
| 0.10% | 1 | 0.087 | 0.13585283963367106 |
| 0.10% | 2 | 0.587 | 0.5759048320875881 |
| 0.10% | 3 | 0.990 | 0.9903285461341728 |
| 1.00% | 0 | 0.111 | 0.1825492835119835 |
| 1.00% | 1 | 0.605 | 0.6341347004291955 |
| 1.00% | 2 | 0.994 | 0.9902575880100868 |
| 1.00% | 3 | 1.000 | 1.0 |
| 5.00% | 0 | 0.429 | 0.46479088992713063 |
| 5.00% | 1 | 0.972 | 0.9710071603027524 |
| 5.00% | 2 | 1.000 | 1.0 |
| 5.00% | 3 | 1.000 | 1.0 |

## Decision

Revise the baseline before implementing DeltaAlign. Although the descriptor assignment substantially exceeds random NC, sparse edits expose descriptor ambiguity and assignment cascades; this experiment does not yet establish high-fidelity localized repair. Inspect descriptor ties and missed changed vertices, then evaluate a stronger structural descriptor on the same saved protocol and seeds. Preserve this baseline as a diagnostic comparison. Do not conclude that all alignment methods lack locality from these results.

No-update checks passed for each seed. Timing covers descriptors, cost construction, and assignment. Five independent seed bundles were used; raw observations remain in results/raw/e00_1k.jsonl. Larger-scale and candidate-closure experiments remain gated on this baseline review.

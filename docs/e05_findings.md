# Update-protocol and objective review findings

Completed 560 method observations on 80 independently reset paired-condition trials: five fresh seeds 25–29, two initial-noise conditions, four requested update fractions, two protocols, and seven methods. Corrected normalization and the frozen E02 policy are unchanged. Noise/protocol conditions share graph/permutation/source-batch seeds; the independent replicates are the five seed bundles, not the 80 condition rows.

Shared evolution preserves the exact XOR observation-noise mask. Independent balanced edits use the same source batch and a separate target batch. Both have matched effective source/target counts. All mask, actual-budget, cost/candidate-refresh, bijection, candidate feasibility, frozen-map, and objective-ordering checks pass.

The hidden permutation is used only in data generation and evaluation. The detector/assignment inputs contain graphs, descriptors, candidate costs, and the old alignment. No stream, boundary/stability term, policy selection, or end-to-end speedup is introduced.

## At requested 0.1% combined-edge updates

| Initial noise | Protocol | Method | RF | FRA | NC | S3 | Relative J gap | Old errors corrected / correct matches broken |
|---|---|---|---|---|---|---|---|---|
| 1% | shared_latent | selected_pruned | 7.28% | 99.60% | 99.14% | 96.99% | 0.23% | 0 / 0 |
| 1% | shared_latent | selected_dense | 7.28% | 99.62% | 99.16% | 97.03% | 0.10% | 1 / 0 |
| 1% | shared_latent | unpruned_k5 | 96.68% | 99.56% | 99.06% | 96.67% | 0.16% | 2 / 6 |
| 1% | shared_latent | unpruned_region_dense | 96.68% | 99.96% | 98.92% | 93.11% | 0.00% | 3 / 14 |
| 1% | shared_latent | local2 | 30.52% | 99.74% | 99.04% | 93.36% | 0.03% | 1 / 6 |
| 1% | shared_latent | keep_old | 0.00% | 99.60% | 99.14% | 96.99% | 0.23% | 0 / 0 |
| 1% | shared_latent | full | 100.00% | 100.00% | 98.88% | 93.07% | 0.00% | 3 / 16 |
| 1% | independent | selected_pruned | 13.54% | 98.48% | 99.14% | 96.79% | 2.27% | 0 / 0 |
| 1% | independent | selected_dense | 13.54% | 98.70% | 98.82% | 95.95% | 0.54% | 2 / 18 |
| 1% | independent | unpruned_k5 | 99.22% | 98.54% | 98.80% | 95.74% | 0.62% | 0 / 17 |
| 1% | independent | unpruned_region_dense | 99.22% | 99.96% | 98.18% | 91.46% | 0.04% | 8 / 56 |
| 1% | independent | local2 | 60.12% | 98.64% | 98.52% | 92.27% | 0.31% | 1 / 32 |
| 1% | independent | keep_old | 0.00% | 98.48% | 99.14% | 96.79% | 2.27% | 0 / 0 |
| 1% | independent | full | 100.00% | 100.00% | 98.20% | 91.51% | 0.00% | 9 / 56 |
| 5% | shared_latent | selected_pruned | 15.88% | 94.72% | 85.08% | 67.07% | 0.83% | 0 / 2 |
| 5% | shared_latent | selected_dense | 15.88% | 95.12% | 85.02% | 66.73% | 0.40% | 12 / 17 |
| 5% | shared_latent | unpruned_k5 | 93.68% | 94.74% | 84.40% | 65.79% | 0.51% | 6 / 42 |
| 5% | shared_latent | unpruned_region_dense | 93.68% | 97.64% | 84.48% | 65.99% | 0.11% | 51 / 83 |
| 5% | shared_latent | local2 | 33.48% | 95.34% | 85.08% | 66.69% | 0.40% | 20 / 22 |
| 5% | shared_latent | keep_old | 0.00% | 94.74% | 85.12% | 67.13% | 0.85% | 0 / 0 |
| 5% | shared_latent | full | 100.00% | 100.00% | 84.16% | 65.71% | 0.00% | 63 / 111 |
| 5% | independent | selected_pruned | 20.70% | 92.48% | 85.08% | 66.98% | 1.18% | 0 / 2 |
| 5% | independent | selected_dense | 20.70% | 92.82% | 84.54% | 66.18% | 0.56% | 22 / 51 |
| 5% | independent | unpruned_k5 | 97.82% | 92.42% | 84.22% | 65.14% | 0.80% | 11 / 56 |
| 5% | independent | unpruned_region_dense | 97.82% | 98.28% | 83.34% | 64.34% | 0.03% | 67 / 156 |
| 5% | independent | local2 | 60.10% | 93.46% | 84.16% | 65.42% | 0.37% | 24 / 72 |
| 5% | independent | keep_old | 0.00% | 92.50% | 85.12% | 67.03% | 1.21% | 0 / 0 |
| 5% | independent | full | 100.00% | 100.00% | 83.06% | 64.17% | 0.00% | 74 / 177 |

Correction/break counts are totals across five 1K graphs, whereas quality values are per-seed means. Cases with no full mapping changes are counted explicitly in the aggregate JSON. Full-objective improvement is not evidence of improving the hidden identity mapping.

## Unchanged sparse guide, including the keep-old control

| Noise | Protocol | Method | Guide met | Worst mean RF | Lowest mean FRA | Largest mean J gap |
|---|---|---|---|---|---|---|
| 1% | shared_latent | selected_pruned | True | 7.28% | 99.60% | 0.23% |
| 1% | shared_latent | selected_dense | True | 7.28% | 99.62% | 0.10% |
| 1% | shared_latent | local2 | False | 30.52% | 99.74% | 0.03% |
| 1% | shared_latent | keep_old | True | 0.00% | 99.60% | 0.23% |
| 1% | independent | selected_pruned | False | 13.54% | 98.48% | 2.27% |
| 1% | independent | selected_dense | False | 13.54% | 98.70% | 0.54% |
| 1% | independent | local2 | False | 60.12% | 98.64% | 0.31% |
| 1% | independent | keep_old | False | 0.00% | 98.48% | 2.27% |
| 5% | shared_latent | selected_pruned | False | 15.88% | 94.72% | 0.83% |
| 5% | shared_latent | selected_dense | False | 15.88% | 95.12% | 0.40% |
| 5% | shared_latent | local2 | False | 33.48% | 95.34% | 0.40% |
| 5% | shared_latent | keep_old | False | 0.00% | 94.74% | 0.85% |
| 5% | independent | selected_pruned | False | 20.70% | 92.48% | 1.18% |
| 5% | independent | selected_dense | False | 20.70% | 92.82% | 0.56% |
| 5% | independent | local2 | False | 60.10% | 93.46% | 0.37% |
| 5% | independent | keep_old | False | 0.00% | 92.50% | 1.21% |

These are internal descriptive guides, not publication thresholds. Meeting them does not establish repair value if keep-old already meets them. Exact mapping differences can still include ties; J gaps and actual error corrections are reported alongside FRA.

## Matched budgets and noise behavior

| Noise | Protocol | Requested fraction | Mean realized fraction | Mean full mapping changes | Zero-change trials | Mean changed noise-mask edges |
|---|---|---|---|---|---|---|
| 1% | independent | 0.01% | 0.0334% | 0.4 | 4/5 | 2.0 |
| 1% | independent | 0.10% | 0.1003% | 15.2 | 0/5 | 6.0 |
| 1% | independent | 1.00% | 1.0030% | 198.4 | 0/5 | 59.6 |
| 1% | independent | 5.00% | 5.0150% | 658.0 | 0/5 | 296.4 |
| 1% | shared_latent | 0.01% | 0.0334% | 0.0 | 5/5 | 0.0 |
| 1% | shared_latent | 0.10% | 0.1003% | 4.0 | 3/5 | 0.0 |
| 1% | shared_latent | 1.00% | 1.0030% | 38.6 | 0/5 | 0.0 |
| 1% | shared_latent | 5.00% | 5.0150% | 56.4 | 0/5 | 0.0 |
| 5% | independent | 0.01% | 0.0334% | 27.6 | 0/5 | 2.0 |
| 5% | independent | 0.10% | 0.1003% | 75.0 | 0/5 | 6.0 |
| 5% | independent | 1.00% | 1.0030% | 292.2 | 0/5 | 60.0 |
| 5% | independent | 5.00% | 5.0150% | 636.0 | 0/5 | 295.6 |
| 5% | shared_latent | 0.01% | 0.0334% | 25.0 | 0/5 | 0.0 |
| 5% | shared_latent | 0.10% | 0.1003% | 52.6 | 0/5 | 0.0 |
| 5% | shared_latent | 1.00% | 1.0030% | 188.8 | 0/5 | 0.0 |
| 5% | shared_latent | 5.00% | 5.0150% | 246.0 | 0/5 | 0.0 |

## Decision, contribution scope, and paper readiness

Shared evolution supplies a low-noise regime with small-region, low-objective-gap repair. The no-repair control is already close to the full solution in that regime, so this is not yet a substantial incremental-repair contribution. More initial noise exposes imperfect prior correspondences and larger mapping churn; the frozen compact/pruned policies do not consistently recover the full behavior. Full descriptor optimization can correct some old errors while breaking more previously correct matches. The same descriptor objective should therefore not be presented as a proven ground-truth/edge-quality improvement.

Use stated-objective maintenance as the provisional technical claim, with NC/S3 and keep-old as quality controls. Explicitly distinguish shared-latent evolution from unpaired observation changes in all future reporting. Any later boundary/stability objective must have a comparable full reference, and must demonstrate something beyond merely retaining the old alignment. The present row-best candidate policy is not the mechanism to scale.

Next establish a compatible dynamic-assignment reference and an assignment-aware localization design. Review the original algorithm/source and its assumptions, implement and verify a small assignment-repair baseline on exactly these changed costs, and compare its full-objective fidelity and complete graph-to-cost/solver work with FullAlign and keep-old. Use fresh seeds for new settings. This directly addresses whether graph-specific localization adds value beyond existing assignment reuse, and avoids another uninformed margin sweep. Do not invent novelty claims before checking that literature.

Paper progress: closer to a defensible problem formulation and useful operating-regime evidence. Still lacking a demonstrated nontrivial localized mechanism, end-to-end efficiency, cross-topology/update-pattern robustness, repeated-stream stability, parallel scaling, and verified novelty. A low-noise condition where keep-old nearly solves the problem cannot by itself justify the intended method paper.

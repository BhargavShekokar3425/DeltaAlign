# Restricted-repair objective and quality findings

Completed 840 method observations on 120 reset update trials: five observed replay seeds (10–14) and five fresh fixed-policy seeds (15–19). The original frozen E02 detector/config/development hashes were verified. Every replay region/miss/candidate-exclusion matched E02. All restricted solves preserve bijection, old-match feasibility, and frozen mappings. Dense updated costs matched the reference.

Seven methods share the same updated objective, descriptors, graph pairs, and batches. Full objective includes frozen rows. Old-match feasibility makes keeping the old mapping an available solution; checks establish J_full <= J_repair <= J_old. Selected dense repair cannot be worse in objective than selected pruned repair. This isolates candidate pruning from region restriction.

Timings are matrix/mask construction and assignment only, using full descriptors and dense cost oracles. They are not end-to-end update latency or incremental speedup. Both-graph one-edit cases duplicate source-only conditions and are not independent repetitions.

## Fresh sparse-update quality

| Side | Requested update | Method | RF | FRA | NC | S3 | Relative J gap | Available J gain recovered |
|---|---|---|---|---|---|---|---|---|
| source | 0.01% | selected_pruned | 2.14% | 100.00% | 99.42% | 97.56% | 0.00% | undefined |
| source | 0.01% | selected_dense | 2.14% | 100.00% | 99.42% | 97.56% | 0.00% | undefined |
| source | 0.01% | unpruned_k5 | 83.04% | 100.00% | 99.42% | 97.56% | 0.00% | undefined |
| source | 0.01% | unpruned_region_dense | 83.04% | 100.00% | 99.42% | 97.56% | 0.00% | undefined |
| source | 0.01% | local2 | 13.00% | 100.00% | 99.42% | 97.56% | 0.00% | undefined |
| source | 0.01% | keep_old | 0.00% | 100.00% | 99.42% | 97.56% | 0.00% | undefined |
| source | 0.01% | full | 100.00% | 100.00% | 99.42% | 97.56% | 0.00% | undefined |
| source | 0.10% | selected_pruned | 11.58% | 94.72% | 99.30% | 96.42% | 60.90% | 10.16% |
| source | 0.10% | selected_dense | 11.58% | 95.68% | 95.96% | 87.00% | 4.46% | 80.62% |
| source | 0.10% | unpruned_k5 | 95.70% | 93.92% | 94.56% | 82.03% | 8.53% | 77.04% |
| source | 0.10% | unpruned_region_dense | 95.70% | 98.88% | 94.76% | 85.01% | 0.17% | 99.40% |
| source | 0.10% | local2 | 54.80% | 95.70% | 95.56% | 86.02% | 5.90% | 80.77% |
| source | 0.10% | keep_old | 0.00% | 94.60% | 99.42% | 97.39% | 64.70% | 0.00% |
| source | 0.10% | full | 100.00% | 100.00% | 94.58% | 84.73% | 0.00% | 100.00% |
| target | 0.01% | selected_pruned | 4.16% | 99.88% | 99.42% | 97.56% | 0.01% | 0.00% |
| target | 0.01% | selected_dense | 4.16% | 99.88% | 99.42% | 97.56% | 0.01% | 0.00% |
| target | 0.01% | unpruned_k5 | 89.78% | 99.88% | 99.42% | 97.56% | 0.01% | 0.00% |
| target | 0.01% | unpruned_region_dense | 89.78% | 99.96% | 99.50% | 97.71% | 0.00% | 50.00% |
| target | 0.01% | local2 | 13.80% | 99.88% | 99.42% | 97.56% | 0.01% | 0.00% |
| target | 0.01% | keep_old | 0.00% | 99.88% | 99.42% | 97.56% | 0.01% | 0.00% |
| target | 0.01% | full | 100.00% | 100.00% | 99.46% | 97.64% | 0.00% | 100.00% |
| target | 0.10% | selected_pruned | 19.00% | 99.30% | 99.42% | 97.41% | 0.13% | 0.00% |
| target | 0.10% | selected_dense | 19.00% | 99.42% | 99.10% | 96.84% | 0.07% | 46.79% |
| target | 0.10% | unpruned_k5 | 99.58% | 99.46% | 99.26% | 97.07% | 0.12% | 51.34% |
| target | 0.10% | unpruned_region_dense | 99.58% | 100.00% | 99.06% | 96.82% | 0.00% | 100.00% |
| target | 0.10% | local2 | 62.02% | 99.38% | 99.12% | 96.80% | 0.05% | 54.65% |
| target | 0.10% | keep_old | 0.00% | 99.30% | 99.42% | 97.41% | 0.13% | 0.00% |
| target | 0.10% | full | 100.00% | 100.00% | 99.06% | 96.82% | 0.00% | 100.00% |
| both | 0.01% | selected_pruned | 2.14% | 100.00% | 99.42% | 97.56% | 0.00% | undefined |
| both | 0.01% | selected_dense | 2.14% | 100.00% | 99.42% | 97.56% | 0.00% | undefined |
| both | 0.01% | unpruned_k5 | 83.04% | 100.00% | 99.42% | 97.56% | 0.00% | undefined |
| both | 0.01% | unpruned_region_dense | 83.04% | 100.00% | 99.42% | 97.56% | 0.00% | undefined |
| both | 0.01% | local2 | 13.00% | 100.00% | 99.42% | 97.56% | 0.00% | undefined |
| both | 0.01% | keep_old | 0.00% | 100.00% | 99.42% | 97.56% | 0.00% | undefined |
| both | 0.01% | full | 100.00% | 100.00% | 99.42% | 97.56% | 0.00% | undefined |
| both | 0.10% | selected_pruned | 14.88% | 98.24% | 99.38% | 97.37% | 11.72% | 2.56% |
| both | 0.10% | selected_dense | 14.88% | 98.46% | 98.40% | 95.04% | 1.23% | 68.91% |
| both | 0.10% | unpruned_k5 | 98.56% | 97.90% | 97.82% | 93.17% | 1.71% | 44.48% |
| both | 0.10% | unpruned_region_dense | 98.56% | 100.00% | 98.14% | 94.18% | 0.00% | 100.00% |
| both | 0.10% | local2 | 60.40% | 98.56% | 98.34% | 94.41% | 1.93% | 76.64% |
| both | 0.10% | keep_old | 0.00% | 98.22% | 99.42% | 97.39% | 12.17% | 0.00% |
| both | 0.10% | full | 100.00% | 100.00% | 98.14% | 94.18% | 0.00% | 100.00% |

## Candidate loss versus region loss

Same selected region, identical dense objective. Absolute losses are sums of squared normalized descriptor distances:

| Side | Requested update | Candidate restriction loss | Region restriction loss |
|---|---|---|---|
| both | 0.01% | 0.000000 | 0.000000 |
| both | 0.10% | 472.631230 | 50.387751 |
| source | 0.01% | 0.000000 | 0.000000 |
| source | 0.10% | 1711.081486 | 142.537276 |
| target | 0.01% | 0.000000 | 0.608858 |
| target | 0.10% | 3.228427 | 4.336648 |

Losses decompose as J_selected_pruned-J_full = (J_selected_pruned-J_selected_dense) + (J_selected_dense-J_full). Exact full-mapping agreement and hidden-truth correctness remain separate: the best descriptor assignment can lose NC after unpaired noisy graph updates even when its objective improves. Keep-old is essential for exposing that distinction.

## Predeclared descriptive quality review

The protocol recorded mean RF <=20%, FRA >=99%, mean NC/S3 loss <=0.5 percentage points, and relative gap <=1% per sparse side/fraction group before E03 outcomes. These are internal guides for more validation, not a revised detection gate or scientific success claim.

| Method | Passes combined guide | Worst group RF | Lowest group mean FRA | Largest group mean J gap |
|---|---|---|---|---|
| selected_pruned | False | 19.00% | 94.72% | 60.90% |
| selected_dense | False | 19.00% | 95.68% | 4.46% |
| unpruned_k5 | False | 99.58% | 93.92% | 8.53% |
| unpruned_region_dense | False | 99.58% | 98.88% | 0.17% |
| local2 | False | 62.02% | 95.70% | 5.90% |
| keep_old | False | 0.00% | 94.60% | 64.70% |
| full | False | 100.00% | 100.00% | 0.00% |

At 0.1% source updates on fresh seeds:

- Selected region RF: 11.58%; dense-within-region objective gap: 4.46%; pruned objective gap: 60.90%.
- Keep-old NC/S3: 99.42%/97.39%; full recomputation NC/S3: 94.58%/84.73%.

The discrepancy is important: reproducing this descriptor optimum and preserving hidden truth/edges are different goals. High NC alone can be achieved by doing no repair in this fixed-identity noisy-copy protocol. The combined guide includes RF, so failure of the full reference on that guide reflects global work, not inaccurate optimization.

## Normalization audit

The inherited scale rule sets initially constant dimensions to 1e-12. A previously empty degree bin becoming variable can therefore dominate squared distances. This audit preserves the original objective/detector and marks affected cases rather than silently fixing them inside the frozen comparison.

| Update | Cases with newly variable floor dimensions | Cases with full J > 1e20 | Trials |
|---|---|---|---|
| 0.01% | 0 | 0 | 30 |
| 0.10% | 0 | 0 | 30 |
| 1.00% | 6 | 6 | 30 |
| 5.00% | 24 | 24 | 30 |

Affected stress objectives must not support quality/crossover claims until normalization is corrected. Next fix the treatment of constant dimensions with a documented finite scale, run regression checks, and repeat fixed-policy baseline/repair comparisons under the revised objective on fresh seeds. Also review why descriptor-objective improvements reduce NC/S3 relative to keep-old. Freeze these choices before further localization work; do not tune pruning margins to hide the failure.

## Decision and paper readiness

The compact frozen-policy diagnostic does not meet the combined quality guide. This moves the project closer to a defensible research conclusion by measuring the failure, but does not advance the central claim of compact, efficient, high-fidelity repair. Broad repair can improve objective fidelity at the cost of near-global regions; keeping old matches must be considered when interpreting high NC.

After correcting the normalization issue and reviewing the objective against keep-old, revisit the localization/assignment interface rather than sweeping more row-best margins: determine whether permutation-cycle competition can be represented by objective-aware candidate dependencies with a correctness or approximation argument. Compare any revised mechanism with a compatible dynamic assignment baseline. Before a new method implementation, inspect individual worst cases and define a fixed validation protocol. If no credible mechanism emerges, test the limitations across topologies and position the work as an empirical characterization rather than claiming an efficient repair algorithm.

Only one graph family, one observation-noise setting, and small independent batches have been tested. End-to-end speedup, scaling, repeated-stream stability, boundary/stability ablations, dynamic-assignment comparison, and verified novelty positioning remain absent. No acceptance probability, readiness percentage, or publication guarantee is justified. Replay results, stress fractions, per-seed failures, and maximum relative gaps are retained in raw/aggregate artifacts.

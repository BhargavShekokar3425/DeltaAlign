# Margin pruning and confidence-seed findings

## Prior evidence and controlled experiment

E01 K=5 closure needed about 95% of the graph for approximately 97% recall at 0.1% source updates. E02 changes candidate and seed admission while preserving descriptors, frozen normalization, graph generation, and edit rules. It remains a detection-only study with dense cached costs and a full descriptor oracle.

Development: 3720 observations, 60 policy settings plus two controls on 60 reset trials (seeds 0–4). Validation: 180 observations, one frozen setting plus two controls on 60 fresh reset trials (seeds 10–14). Both-graph one-edit trials duplicate source-only trials and are reported separately, not pooled as independent evidence.

All cached cost, ranking, and candidate comparisons matched full refresh. Every retained list includes its old match; closure target-separation assertions passed. No mapping or optimum truth was used to construct the detector.

## Frozen selection

Selected cap K=20, mean-per-feature cost margin=0, seed policy=confidence, pressure threshold=0.1.

Selection status: `exploratory_development_gate_failed`. Qualifying development settings: 0 of 60. Configuration, detector-source, and development-result hashes were saved before validation; validation checked the config and source hashes. Validation gate passed: **False**.

The development rule sought <=20% worst-group mean RF, >=95% group mean recall, >=90% minimum nonempty-trial recall, and no changed full-match target excluded from candidates. These are internal guides. If none qualified, the frozen choice maximized recall under the RF budget; if no setting fit that budget, it minimized worst-group RF. Either fallback is explicitly exploratory.

| Stage | Side | Requested update | Method | Seed RF | Final RF | Recall | Changed-target coverage | Nonempty |
|---|---|---|---|---|---|---|---|---|
| development | both | 0.01% | selected | 1.84% | 3.24% | 33.33% | 52.78% | 3/5 |
| development | both | 0.10% | selected | 9.12% | 15.60% | 79.72% | 29.17% | 3/5 |
| development | source | 0.01% | selected | 1.84% | 3.24% | 33.33% | 52.78% | 3/5 |
| development | source | 0.10% | selected | 7.20% | 12.92% | 52.26% | 13.19% | 4/5 |
| development | target | 0.01% | selected | 2.10% | 3.66% | 25.00% | 12.50% | 2/5 |
| development | target | 0.10% | selected | 12.16% | 20.62% | 62.50% | 20.83% | 3/5 |
| development | both | 0.01% | radius2 | 12.96% | 12.96% | 72.22% | undefined | 3/5 |
| development | both | 0.10% | radius2 | 56.72% | 56.72% | 81.71% | undefined | 3/5 |
| development | source | 0.01% | radius2 | 12.96% | 12.96% | 72.22% | undefined | 3/5 |
| development | source | 0.10% | radius2 | 58.70% | 58.70% | 71.64% | undefined | 4/5 |
| development | target | 0.01% | radius2 | 13.38% | 13.38% | 37.50% | undefined | 2/5 |
| development | target | 0.10% | radius2 | 61.78% | 61.78% | 66.67% | undefined | 3/5 |
| development | both | 0.01% | unpruned_k5 | 12.96% | 83.90% | 97.22% | 77.78% | 3/5 |
| development | both | 0.10% | unpruned_k5 | 82.40% | 98.12% | 99.12% | 48.18% | 3/5 |
| development | source | 0.01% | unpruned_k5 | 12.96% | 83.90% | 97.22% | 77.78% | 3/5 |
| development | source | 0.10% | unpruned_k5 | 58.70% | 94.82% | 96.76% | 49.19% | 4/5 |
| development | target | 0.01% | unpruned_k5 | 38.56% | 89.78% | 100.00% | 25.00% | 2/5 |
| development | target | 0.10% | unpruned_k5 | 94.46% | 99.48% | 100.00% | 54.17% | 3/5 |
| validation | both | 0.01% | selected | 1.40% | 2.56% | 19.87% | 40.38% | 2/5 |
| validation | both | 0.10% | selected | 9.04% | 16.14% | 58.64% | 21.06% | 5/5 |
| validation | source | 0.01% | selected | 1.40% | 2.56% | 19.87% | 40.38% | 2/5 |
| validation | source | 0.10% | selected | 9.38% | 15.88% | 65.11% | 28.54% | 5/5 |
| validation | target | 0.01% | selected | 2.50% | 4.36% | 55.56% | 33.33% | 1/5 |
| validation | target | 0.10% | selected | 11.22% | 19.68% | 46.92% | 37.15% | 5/5 |
| validation | both | 0.01% | radius2 | 11.76% | 11.76% | 16.03% | undefined | 2/5 |
| validation | both | 0.10% | radius2 | 60.32% | 60.32% | 65.43% | undefined | 5/5 |
| validation | source | 0.01% | radius2 | 11.76% | 11.76% | 16.03% | undefined | 2/5 |
| validation | source | 0.10% | radius2 | 66.28% | 66.28% | 81.91% | undefined | 5/5 |
| validation | target | 0.01% | radius2 | 12.38% | 12.38% | 55.56% | undefined | 1/5 |
| validation | target | 0.10% | radius2 | 60.50% | 60.50% | 66.54% | undefined | 5/5 |
| validation | both | 0.01% | unpruned_k5 | 11.76% | 80.96% | 96.15% | 60.26% | 2/5 |
| validation | both | 0.10% | unpruned_k5 | 85.84% | 98.34% | 99.67% | 50.19% | 5/5 |
| validation | source | 0.01% | unpruned_k5 | 11.76% | 80.96% | 96.15% | 60.26% | 2/5 |
| validation | source | 0.10% | unpruned_k5 | 66.28% | 96.18% | 97.52% | 57.87% | 5/5 |
| validation | target | 0.01% | unpruned_k5 | 36.78% | 88.40% | 100.00% | 100.00% | 1/5 |
| validation | target | 0.10% | unpruned_k5 | 92.36% | 98.96% | 100.00% | 70.19% | 5/5 |

## Meaning and limits

Region recall and candidate coverage are separate necessary conditions for matching the dense reference: a changed vertex may be detected while its full target has been pruned. Mean changed-target coverage reports that distinction. The grouped JSON also reports an analytical upper bound on FRA from the union of missed vertices and excluded targets; this is not observed repair accuracy. A high bound does not establish that a restricted solver attains it.

Row-best margins are sensitive to global assignment competition: a globally optimal match need not be the row-wise nearest target. Confidence filtering reduces seeds but can drop low-pressure vertices required in a permutation cycle. Large-update (1% and 5%) results are retained in raw/grouped files; they were not used to select the sparse-update policy. No speedup, objective-gap, or local-repair quality was measured.

## Decision and next step

The predeclared dense-recovery gate is not satisfied. Do not scale this pruning policy or claim exact-maintenance fidelity. Preserve the negative result: unconditional closure grows too widely, while row-wise pruning and pressure seeds trade recovery for compactness.

Next run a small objective-fidelity diagnostic on the frozen selected region/candidates, the unpruned closure control, and fixed-radius repair. Solve each restricted assignment while retaining old-match edges, then compare NC, S3, FRA, and the same full objective including absolute/relative gaps. Also include repair on the selected region with all old-image targets to separate detection losses from candidate-pruning losses. This tests whether missed dense mappings materially harm quality rather than changing the detection gate after seeing results. It is a diagnostic review of the formulation, not approval to proceed to production/parallel repair. If quality losses remain material, revisit the objective or candidate localization approach. Use fresh evaluation seeds for any new parameter selection; 10–14 are now observed.

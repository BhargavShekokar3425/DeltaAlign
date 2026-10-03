# Constant-bin normalization correction findings

Completed 840 observations per objective mode, 1680 total: paired historical and corrected objectives across 120 reset update trials each. Seeds 15–19 are replay; 20–24 are fresh fixed-policy confirmation. All seven repair/reference methods retain the E02 cap/margin/confidence settings. No objective or detector parameter was selected on these outcomes.

All 420 legacy replay observations exactly match the prior E03 objectives, quality, RF, and FRA. Initial cost matrices are exactly equal between modes on all ten seeds. Constant-bin scale is 1.0 in the corrected mode instead of 1e-12; every other initial standard deviation and all scales after updates remain frozen.

Full-reference costs/candidate-refresh checks and restricted feasibility checks passed. Historical outputs and frozen sources are preserved. The original FullAlign default remains explicitly historical; E04 supplies the corrected scale via src/normalization.py.

## Numerical correction

| Objective mode | Requested update | Active constant-bin cases | Full objectives >1e20 | Max full objective | Trials |
|---|---|---|---|---|---|
| legacy | 0.01% | 0 | 0 | 4940.17 | 30 |
| legacy | 0.10% | 0 | 0 | 6598.55 | 30 |
| legacy | 1.00% | 4 | 4 | 9.5771e+25 | 30 |
| legacy | 5.00% | 28 | 28 | 1.51143e+25 | 30 |
| corrected | 0.01% | 0 | 0 | 4940.17 | 30 |
| corrected | 0.10% | 0 | 0 | 6598.55 | 30 |
| corrected | 1.00% | 4 | 0 | 22305.5 | 30 |
| corrected | 5.00% | 28 | 0 | 76170.9 | 30 |

Of 420 paired sparse method observations, 420 are exactly unchanged on objective, quality, RF, and FRA. This paired comparison distinguishes the fix from fresh-seed variation; the correction cannot be credited for a quality improvement where its dimensions were inactive.

Absolute objectives under different scaling rules are different quantities. Their magnitudes diagnose excessive weighting, not a claim that the corrected optimizer improves the historical objective. Relative gaps below are always evaluated within the corrected objective against its own full recomputation.

## Corrected objective on fresh sparse trials

| Side | Update | Method | RF | FRA | NC | S3 | Relative J gap | J gain recovered |
|---|---|---|---|---|---|---|---|---|
| source | 0.01% | selected_pruned | 2.36% | 99.96% | 98.78% | 96.43% | 0.00% | 0.00% |
| source | 0.01% | selected_dense | 2.36% | 99.96% | 98.78% | 96.43% | 0.00% | 0.00% |
| source | 0.01% | unpruned_k5 | 80.70% | 99.96% | 98.78% | 96.43% | 0.00% | 0.00% |
| source | 0.01% | unpruned_region_dense | 80.70% | 100.00% | 98.74% | 96.36% | 0.00% | 100.00% |
| source | 0.01% | local2 | 12.30% | 99.96% | 98.78% | 96.43% | 0.00% | 0.00% |
| source | 0.01% | keep_old | 0.00% | 99.96% | 98.78% | 96.43% | 0.00% | 0.00% |
| source | 0.01% | full | 100.00% | 100.00% | 98.74% | 96.36% | 0.00% | 100.00% |
| source | 0.10% | selected_pruned | 11.66% | 94.50% | 98.58% | 95.85% | 27.61% | 20.75% |
| source | 0.10% | selected_dense | 11.66% | 94.86% | 96.08% | 89.41% | 7.88% | 69.77% |
| source | 0.10% | unpruned_k5 | 95.22% | 93.00% | 94.06% | 83.76% | 9.70% | 57.29% |
| source | 0.10% | unpruned_region_dense | 95.22% | 98.06% | 94.72% | 87.04% | 2.39% | 92.59% |
| source | 0.10% | local2 | 64.46% | 95.38% | 95.54% | 88.01% | 6.56% | 83.46% |
| source | 0.10% | keep_old | 0.00% | 94.42% | 98.78% | 96.27% | 27.95% | 0.00% |
| source | 0.10% | full | 100.00% | 100.00% | 94.58% | 86.86% | 0.00% | 100.00% |
| target | 0.01% | selected_pruned | 4.22% | 99.96% | 98.78% | 96.43% | 0.00% | 0.00% |
| target | 0.01% | selected_dense | 4.22% | 99.96% | 98.78% | 96.43% | 0.00% | 0.00% |
| target | 0.01% | unpruned_k5 | 85.70% | 99.92% | 98.74% | 96.43% | 0.00% | 0.00% |
| target | 0.01% | unpruned_region_dense | 85.70% | 100.00% | 98.80% | 96.52% | 0.00% | 100.00% |
| target | 0.01% | local2 | 9.18% | 99.96% | 98.78% | 96.43% | 0.00% | 0.00% |
| target | 0.01% | keep_old | 0.00% | 99.96% | 98.78% | 96.43% | 0.00% | 0.00% |
| target | 0.01% | full | 100.00% | 100.00% | 98.80% | 96.52% | 0.00% | 100.00% |
| target | 0.10% | selected_pruned | 21.46% | 98.58% | 98.78% | 96.28% | 0.33% | 0.00% |
| target | 0.10% | selected_dense | 21.46% | 98.98% | 98.54% | 95.90% | 0.06% | 78.45% |
| target | 0.10% | unpruned_k5 | 99.68% | 98.62% | 98.54% | 95.56% | 0.31% | 8.32% |
| target | 0.10% | unpruned_region_dense | 99.68% | 99.86% | 98.28% | 95.23% | 0.00% | 98.81% |
| target | 0.10% | local2 | 68.54% | 98.56% | 98.54% | 95.65% | 0.13% | 57.10% |
| target | 0.10% | keep_old | 0.00% | 98.58% | 98.78% | 96.28% | 0.33% | 0.00% |
| target | 0.10% | full | 100.00% | 100.00% | 98.18% | 95.07% | 0.00% | 100.00% |
| both | 0.01% | selected_pruned | 2.36% | 99.96% | 98.78% | 96.43% | 0.00% | 0.00% |
| both | 0.01% | selected_dense | 2.36% | 99.96% | 98.78% | 96.43% | 0.00% | 0.00% |
| both | 0.01% | unpruned_k5 | 80.70% | 99.96% | 98.78% | 96.43% | 0.00% | 0.00% |
| both | 0.01% | unpruned_region_dense | 80.70% | 100.00% | 98.74% | 96.36% | 0.00% | 100.00% |
| both | 0.01% | local2 | 12.30% | 99.96% | 98.78% | 96.43% | 0.00% | 0.00% |
| both | 0.01% | keep_old | 0.00% | 99.96% | 98.78% | 96.43% | 0.00% | 0.00% |
| both | 0.01% | full | 100.00% | 100.00% | 98.74% | 96.36% | 0.00% | 100.00% |
| both | 0.10% | selected_pruned | 18.48% | 97.58% | 98.74% | 96.22% | 13.01% | 0.24% |
| both | 0.10% | selected_dense | 18.48% | 97.98% | 97.72% | 93.81% | 1.61% | 54.12% |
| both | 0.10% | unpruned_k5 | 98.28% | 97.12% | 97.66% | 92.97% | 4.45% | 40.18% |
| both | 0.10% | unpruned_region_dense | 98.28% | 99.78% | 97.30% | 92.80% | 0.03% | 80.72% |
| both | 0.10% | local2 | 60.84% | 97.66% | 97.36% | 92.72% | 2.71% | 49.63% |
| both | 0.10% | keep_old | 0.00% | 97.56% | 98.78% | 96.27% | 13.07% | 0.00% |
| both | 0.10% | full | 100.00% | 100.00% | 97.34% | 92.88% | 0.00% | 100.00% |

## Frozen quality-guide review

| Method | Meets combined sparse guide on fresh seeds | Worst group RF | Lowest group FRA | Largest group J gap |
|---|---|---|---|---|
| selected_pruned | False | 21.46% | 94.50% | 27.61% |
| selected_dense | False | 21.46% | 94.86% | 7.88% |
| unpruned_k5 | False | 99.68% | 93.00% | 9.70% |
| unpruned_region_dense | False | 99.68% | 98.06% | 2.39% |
| local2 | False | 68.54% | 95.38% | 6.56% |
| keep_old | False | 0.00% | 94.42% | 27.95% |
| full | False | 100.00% | 100.00% | 0.00% |

Guides are unchanged from E03 (RF <=20%, FRA >=99%, NC/S3 loss <=0.5 percentage points, J gap <=1% per sparse group). Full-reference failure on this combined guide reflects RF=100%, not an optimization defect. The detection gate from E02 remains failed.

## Objective versus truth/structure

At 0.1% fresh source updates, selected dense repair uses 11.66% RF with 7.88% J gap; selected pruned repair has 27.61% J gap.

Keep-old NC/S3 is 98.78%/96.27%, compared with full NC/S3 94.58%/86.86%. This is a measured distinction between preserving fixed hidden identities and minimizing descriptor cost. Fixing scale weighting is not, by itself, a fix for that objective/quality mismatch.

A mean absolute-gap difference between selected pruned and selected dense repair isolates candidate exclusion; selected dense versus full isolates frozen-region restrictions. Those quantities, maximum per-group gaps, replay breakdowns, and 1%/5% stress quality are retained in the aggregate JSON.

## Decision and paper readiness

The compact frozen diagnostic still does not meet the combined quality guides. The numerical correction is real scientific-reliability progress, but it does not rescue the localization/pruning policy or establish a publishable efficient-repair method. The new fresh-seed evidence must not be presented as an improvement caused by normalization without the paired comparison.

Next freeze an objective/update-protocol review: compare the existing unpaired source/target observation edits with shared-latent paired graph evolution plus persistent observation noise, retaining keep-old and the same frozen repair controls. Include a higher initial-noise condition to test whether updates can correct an imperfect old alignment. Separate objective maintenance, ground-truth improvement, and churn before developing a new localization mechanism. Use fresh seeds and no margin tuning. Preserve these controls when adding boundary/stability scoring; those terms require explicitly comparable objectives.

Paper status: closer to trustworthy experiments and a clear statement of limitations. Still missing a justified localized dependency mechanism, a validated quality/maintenance claim, end-to-end speedup, cross-topology/update-pattern evidence, streams, parallel scaling, dynamic-assignment comparison, and verified novelty. No readiness percentage or acceptance probability is warranted. Solver-only timings remain diagnostic and do not measure incremental efficiency.

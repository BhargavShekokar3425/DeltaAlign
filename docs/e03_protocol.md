# E03 restricted-repair quality diagnostic

## Reason for this experiment

E01 unpruned closure recovered most dense mapping changes by touching almost the whole graph. E02 row-best margin pruning/confidence seeds reduced the region, but failed detection and candidate-coverage gates. A missed dense mapping does not quantify objective or biological/structural quality loss. E03 solves restricted assignments to measure that loss without tuning the failed detector or relaxing its detection gate retrospectively.

## Frozen settings and seed groups

Load the original E02 selection (K=20, margin=0, confidence pressure >0.1). Verify its original source hashes and E02 config/result hashes before replay. Do not rerun selection. Reproduce graph generation, update side allocation, candidate maintenance, cost scaling, and seed rules exactly. Use observed seeds 10–14 as replay diagnostics and fresh seeds 15–19 as confirmation of the fixed comparison. Report separately. Both/source one-edit duplicates remain labeled and are not pooled as independent evidence.

Use 1K BA graphs, attachment 3, 1% target noise, two-hop histograms, frozen initial scaling, and combined-edge fractions 0.01%, 0.1%, 1%, 5%. Full descriptors and dense cost matrices remain reference oracles; no speedup claim is possible from solver-only timings.

## Methods compared on identical updated costs

1. Selected pruned: E02 region and allowed candidates; freeze all outside mappings.
2. Selected dense: same region, allow every old-image target. The objective difference from method 1 isolates candidate restriction loss.
3. Unpruned K=5: E01-style support/dependency closure and top-K plus old-match candidate constraints.
4. Unpruned region dense: same larger region but all old-image targets; separates candidate restriction from region size for that control.
5. Local-2: radius-2 source support plus inverse mapped target support, all old-image targets.
6. Keep-old: no repair, evaluated on updated graphs and costs. This essential control tests whether repair does better than retaining an already high-NC alignment. Fixed hidden identity means old NC remains unchanged; retaining NC alone does not validate maintenance.
7. FullAlign: exact global assignment, with identical descriptors, normalization, and objective.

For each restricted solve, map A bijectively onto M_old(A). Keep old-match edges; verify feasibility, bijection, candidate membership, and frozen mappings. Compute global J=sum_u D_new(u,M(u)), including frozen rows, for all methods. Verify J_full <= J_repair <= J_old within numerical tolerance. Verify dense selected-region cost <= pruned selected-region cost. Their losses decompose as J_pruned-J_full = (J_pruned-J_dense_region) + (J_dense_region-J_full).

Log absolute/relative gaps, FRA, churn, NC, EC, S3, and objective improvement relative to keep-old. Relative gap is undefined if J_full=0; fraction of available objective gain is undefined if the keep-old/full difference is negligible. Give seed-level distributions and per-side mean/max values. Distinguish descriptive review guides from passed scientific claims: <=20% mean RF, >=99% mean FRA, <=0.5 percentage-point mean NC/S3 losses, <=1% mean relative objective gap in each nonempty sparse group would motivate more validation. These new quality guides do not erase E02's failed detection gate and are recorded before E03 outcomes.

Metadata records configuration, original selection, and current source hashes. Timings cover restricted matrix/mask construction and assignment only. Feature maintenance, candidate search, detection, validation, and metric work remain excluded; report no end-to-end speedup. Parameter selection, CPU scaling, and stream claims remain outside scope.

## Paper-readiness reporting

After this and future experiments, explicitly state whether the evidence moves DeltaAlign closer to a defensible paper. Distinguish reproducible tooling from demonstrated method contribution. Report remaining gaps in localization, comparable quality, end-to-end efficiency, robustness, streams, and novelty verification. Do not invent readiness percentages or acceptance probabilities.

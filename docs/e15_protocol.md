# E15 preregistration: attribute gains beyond conservative locality

Status: preregistered and completed on 2026-10-03. See [findings](e15_findings.md). The frozen configuration retains its original preregistration status; execution completion is recorded in the aggregate. Motivation is the missing control identified in [E14](literature_component_audit.md), especially affected-neighborhood recomputation in incremental graph inference. This experiment is not a reproduction of InkStream/RIPPLE++ or a novelty test.

## Fixed question and configuration

Does refined second-layer propagation or actual feature-row filtering save useful work relative to conservative dependency-local maintenance, while retaining exactly the same descriptor objective and compiled solver?

Use five fresh seeds 66–70, n=1,000, BA/ER/WS, initial noise 1%, shared-latent mixed edge updates, requested per-graph fractions 0.1% and 1%, and ten persistent steps. Keep E11/E13 topology generation, hidden permutation, persistent observation mask, half-up budget calculation and seed derivation. Thirty independent size/topology/budget/seed streams, four isolated workers per stream, 300 unique update scenarios and 1,200 method-update observations. Compare each non-full method to full after initialization and each step: 990 paired validation snapshots. Ten steps within a stream are correlated. No hyperparameter tuning or WS-quality-driven exclusions.

## Four methods with one frozen objective

| Method | Descriptor update | Cost update | Assignment |
|---|---|---|---|
| Full | Frozen full descriptor computation | Full normalized squared-Euclidean cdist | Compiled SciPy |
| Refined | Existing E07 cache with histogram-change propagation and actual dirty-row comparison | Existing E10 disjoint blocks for actual dirty rows/columns | Compiled SciPy |
| Conservative features | Same cache layout, first-layer computation and equality comparison; second layer recomputed on all conservative dependency rows | Existing E10 blocks for actual dirty features | Compiled SciPy |
| Conservative costs | Existing refined descriptor update | Existing E10 blocks using a conservative superset of dirty feature rows/columns | Compiled SciPy |

Define conservative support *before mutating caches*: edited endpoints E; F = E union old/new neighbors of E; S = E union old/new neighbors of all F; T = F union S. For conservative features, update endpoint degrees, recompute basic statistics/histograms on F, recompute second-layer means on S irrespective of actual histogram changes, and compare old/new rows on T. For conservative costs, use T independently on each graph as the cost dirty-set superset. Handle no-change batches and isolated vertices. This is a dependency-local **adaptation**, not an original prior-work implementation.

All maintained methods must have identical initial cache layout and use the same actual initialization path, frozen initial normalization and persistent dense cost lifecycle. The full worker releases obsolete dense costs as in E13. The conservative-cost variant changes only normalized rows and cost entries selected for recomputation. Count support construction and equality filtering in feature timings. Record extra conservative-support construction time explicitly and include it in pipeline time even when required only for the cost variant. Do not charge a comparator for diagnostics the refined method does not need.

## Correctness and measurements

Before benchmarking, test old/new adjacency dependencies, overlapping edits, unchanged histograms/bin crossings, insertions/deletions, no-change batches, isolates and consecutive mixed updates. All methods must agree bitwise with frozen full features, normalization, scale and costs, and have the same compiled mapping/objective under the same ordering. A failed check stops that comparison; do not drop the case and report the remaining successes.

Run sequential fresh workers, alternate/cycle the four method orders across seeds/conditions, record actual order, inspected headroom, software/hardware and source/config hashes. Exactly 30 streams × four workers = 120 workers. Timings exclude graph generation and validation; whole-worker peak RSS includes both. Use contiguous-buffer fingerprints without a full validation cost copy. Required initialization is part of total latency. Keep hidden truth restricted to generation and quality evaluation.

Report first/second-layer support, actual changed histogram/feature counts, rows normalized and unique cost entries computed. Sum ten correlated step timings within each worker before pairing. Report all five seed ratios separately per topology/budget: refined versus conservative features for feature time, refined versus conservative costs for cost time, and all versus full for update-only and setup-inclusive totals. Include median, quartiles, range, worker RSS, initial/final NC/EC/S3 and a plot of second-layer work versus time. No pooled-topology significance claim, stage-only overall claim or nominal speedup target.

## Predeclared interpretation

- Exact component gain over a conservative control counts positively even if solver dominance hides it in total latency or RSS increases.
- If refined propagation saves work but equality/support overhead eliminates feature-time gain, report both; do not infer performance from row counts.
- If either control performs as well as refined maintenance, revise the contribution around simpler locality or retain a reproducible engineering finding. Do not claim a new propagation method from a speedup over full recomputation.
- Near-one differences remain timing-inconclusive without repeated fixed-job execution. This 1K attribution study does not validate E13's small 5K total effects.
- Weak WS quality remains a limit even with exact objective agreement. No accuracy, long-stream, real-data, 10K or parallel result is implied.

Deliver new experiment/control files without changing historical frozen kernels, saved config/raw/aggregate/figure artifacts, tests and `docs/e15_findings.md`. Update contribution decision and paper readiness from all results before scheduling broader workloads.

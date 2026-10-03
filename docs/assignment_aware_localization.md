# Assignment-aware localization after E06

E01's unconditional candidate-owner closure often covered most of the graph. E02's row-best margins missed globally necessary assignments, and E03 showed that pruning added objective loss. E05 showed why keep-old and hidden-truth controls are necessary. E06 now establishes exact assignment reuse using a published primal-dual method; see [provenance and timing boundaries](e06_protocol.md) and [measured results](e06_findings.md).

## What the exact baseline teaches

For costs C, keep the existing bijection and row/column potentials satisfying `u[i] + v[j] <= C[i,j]`, with equality on assigned edges. Changed source descriptors alter cost rows; changed target descriptors alter columns, including previously unconsidered target entrants. Unmatch affected rows and old owners of changed columns, restore dual feasibility, and grow alternating paths until an optimal bijection is restored. The E06 implementation validates global reduced costs and matched-edge tightness afterward.

This process follows assignment competition as needed. It does not require every candidate owner to enter a precomputed repair region. However, E06 at requested 0.1% updates still visits 77.8–97.6% of rows on average, depending on noise/protocol. The exposed set, search set, changed descriptors and final mapping churn must be reported separately. Small graph edits do not imply small exact searches.

These are established assignment techniques, not DeltaAlign novelty. A potential contribution must come from graph-specific maintenance, guaranteed cost search, or valid decomposition with measured benefit beyond this baseline.

## Next implementable step: exact selective descriptor maintenance

Keep fixed vertex IDs, the two-hop histogram descriptor, frozen initial normalization, the dense cost cache and the exact E06 solver. Cache degrees, raw neighbor-degree histograms, basic statistics and second-layer histogram averages. Start with sequential work and compare every result to the existing full descriptor oracle.

For a valid batch, let S contain edge endpoints. Only degrees in S can change. Basic neighbor-degree statistics and first-layer histograms can change at S or at old/new neighbors of S. After updating those histograms, second-layer averages can change at endpoints whose neighbor sets changed and at old/new neighbors of changed histogram rows. This gives a conservative old/new radius-two support; it can be large on BA hubs and should not be called compact without measurement.

Recompute complete statistics for supported rows first, rather than incrementally subtracting floating-point moments. Preserve the oracle's sorted degree values, fixed bins and accumulation behavior. Compare resulting descriptor arrays exactly; if numerical identity cannot be maintained, document the reason and distinguish descriptor approximation from solver errors. Use actual changed feature rows, not just conservative support, for exact dense cost refresh. Record support discovery, cache updates, feature copies, equality detection, cost refresh, assignment repair and total graph-to-assignment time. Include cache initialization and storage separately.

Acceptance requires full feature equality, full refreshed cost equality, a valid bijection and primal-dual certificate, and objective equality with SciPy for every trial. Tests must include insertions, deletions, mixed batches, isolated nodes, hubs, changed degree bins, both graph sides and repeated updates. Benchmark fresh seeds 35–39 under E06's frozen protocols/noise/budgets. Compare full features + dynamic repair, selective features + dynamic repair, compiled full recomputation and keep-old on identical initial states. Report paired timing distributions and crossover; retain NC/S3 as controls.

Success would establish an exact graph-maintenance component. It would not by itself prove novelty, compact assignment repair, scalable memory use or stream performance. A negative timing result should lead to profiling and fallback design, not additional margin tuning.

## Later requirements for sparse search and parallel components

Skipping cost entries requires a lower-bound or search guarantee that no omitted edge can violate dual feasibility or become an improving entrant; old top-K lists alone do not supply this. Global certificate scans are currently quadratic and validation-only. An operational method must count any certificate or index maintenance needed for safe execution.

Parallel components require disjoint target ownership and an argument that omitted cross-component edges cannot improve the objective under the maintained duals. Structural separation alone is insufficient. Preserve old-match feasibility and fall back to full assignment when certified separation or work savings fail. Measure fallback cost, dense-cache memory and initialization before moving to 5K/10K nodes or claiming CPU scaling.


## E07 implementation and revised next comparison

Exact selective maintenance is now implemented in `src/descriptor_cache.py`. It caches degrees, raw histograms and final feature rows, and propagates only actual histogram changes to the second layer. Complete statistics preserve full-oracle numerical equality; both graph sides and repeated-update correctness are checked. See [E07 protocol](e07_protocol.md) and [findings](e07_findings.md).

E07's paired comparison isolates descriptor maintenance while retaining the E06 assignment implementation. The next required control is selective graph/cost maintenance followed by compiled SciPy, on fresh seeds 40–44. Compare it directly with selective dynamic assignment and full compiled recomputation under frozen conditions, including copies and initialization. This separates the benefit of graph maintenance from the benefit of warm assignment reuse. Do not design a favorable fallback from per-trial hindsight. A compiled fallback in a persistent warm solver also needs a measured way to restore reusable dual state; a SciPy permutation alone is insufficient.


## E08 result and next stream gate

The compiled selective control is now complete; see [E08 findings](e08_findings.md). Graph-maintenance gains persist with compiled assignment. Warm reuse remains useful in the sparsest regimes, but its current kernel loses at 1%/5% updates and carries substantial initialization cost. These are measured implementation regimes, not a fallback proof.

Next compare fixed-choice persistent selective-warm and selective-compiled pipelines on ten-step streams (fresh seeds 45–49, requested 0.1%/1%, both protocols/noise levels). Count actual required initialization and every update, validate cache/cost/objective equality at every step, and retain full compiled and keep-initial controls. Remove reset-specific cloning; do not hide needed state copies. Defer solver switching until warm dual restoration is measured. Novelty, broader topology and scaling remain separate gates.


## Reporting component progress

The user explicitly counts a validated improvement in any pipeline component as a better outcome even when whole-pipeline performance does not improve. For every experiment, report feature maintenance, cost maintenance, solver work, update latency and setup-inclusive latency separately. Give component gains positive credit and explain what limits their practical effect. Do not suppress a useful stage improvement because initialization or another stage dominates, and do not describe a stage ratio as an overall speedup. Stream ratios must be computed after summing correlated batches within each independent seed/stream.


## E10 cost-cache evidence

[E10 findings](e10_findings.md) verify dirty-only normalization, disjoint cost blocks and persistent in-place dense updates. Cost stages improve 1.23–1.27× at 0.1% and 1.75–1.77× at 1% versus historical refresh, while setup-inclusive totals improve about 1–7%. Component gains receive positive credit; the remaining full-cost comparison at 1% is still slightly unfavorable. Exact mapping equality leaves quality unchanged. Next test [topology robustness](topology_robustness_design.md) on fresh seeds 55–59 before stronger generality/scaling claims.

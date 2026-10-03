# Paper readiness

Report component, update-only, setup-inclusive and memory outcomes independently. Validated component improvements count positively even where the total outcome is small, variable or worse. No readiness percentages or publication guarantees.

Latest: [E16 repeated fixed-job findings](e16_findings.md). Sixty fresh workers completed; all 120 paired snapshots match E13 exactly; 47 tests pass and historical kernels remain unchanged. Three executions are nested within each fixed seed job, not treated as independent graph samples.

**Closer through calibrated repeatability.** BA setup-inclusive median ratio is 1.039× and all 15 executions favor maintenance. WS median is 1.034× but only 14/15 executions favor it: seed 63 reverses in round 1, so a uniformly robust WS total win remains unsupported. These are small, workload/machine-specific benefits. Component medians persist: BA features/costs 7.79×/1.86×, WS 17.96×/5.37×. Median peak-RSS ratios remain unfavorable at 1.182 BA and 1.058 WS.

| Evidence needed | Current status |
|---|---|
| Exactness/reproducibility | E16 paired and historical fingerprints/objectives exact; frozen kernels, configs, timing/order/thread metadata and 47 tests |
| Component attribution | E15 shows refined feature gains on all 30 streams and sparse cost gains beyond conservative locality; BA 1% bare cost ratio 0.99× remains a counterexample |
| Larger fixed-job timings | BA small saving persists in every repeat; WS generally favors maintenance but has a reversal and one overlapping job timing range |
| Overall scope | E15 1K totals and E13/E16 bounded 5K conditions only; no broad-noise/budget or long-stream scaling claim |
| Memory | Whole-worker RSS measured; repeated 5K medians about 18% BA / 6% WS higher for maintenance; dense costs remain quadratic |
| Objective quality | Identical full mappings; weak WS correspondence remains. No accuracy benefit or new independent quality sample from repetitions |
| Novelty | E14 finds structural histograms, incremental propagation and assignment repair prior art. Timing repeatability does not establish algorithm novelty |
| Real topology / longer streams | Source descriptions checked for a bounded SNAP follow-up; file ingestion/projection and benchmark not yet executed |
| Decomposition/parallelism | Assignment dominates larger cases; no certified independent components or CPU scaling result |

The component-focused empirical case is stronger: exactness, attribution and repeated stage efficiency are supported, with modest BA total savings and an explicit WS exception. A novel scalable parallel alignment paper remains unsupported. Do not erase component improvements because total effects are small, or turn them into accuracy/novelty claims.

Next: [bounded real-topology provenance and initial-quality gate](real_topology_gate.md). Verify immutable raw data, counts, node-preserving projection and identifiers; then preregister a small quality/no-update/maintenance pilot with constructed correspondence clearly labeled. Retain negative real-topology quality/locality outcomes rather than tune on evaluation seeds. Longer streams, broader prior-work compatibility and certified CPU decomposition remain future gates.

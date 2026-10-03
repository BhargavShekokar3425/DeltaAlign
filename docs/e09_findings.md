# E09 findings: persistent-state stream pilot

Completed 40 ten-batch streams, 400 updates and 1600 method observations on fresh seeds 45–49. All selective features, actual dirty sets and costs match full recomputation at every step; selective SciPy returns the full SciPy mapping. All 400 warm updates pass global primal-dual certificates and match the optimal objective. Maximum absolute objective difference is 0. Shared-latent observation masks are checked against the initial mask at every step. The protocol was saved before execution, and historical kernels/results remain frozen.

Each method initializes its own required state, then maintains it across ten successive updates. No reset-specific state/cache clones occur per batch. Warm repair still copies refreshed costs internally; selective cost refresh still copies dense costs. Timings start from already updated graphs and exclude generation, batch application, validation and quality evaluation. Setup-inclusive totals include real method-specific feature/cost/solver setup. Keep-initial pays initial full alignment and does no update computation.

Five stream/seed bundles per condition provide independent observations; correlated batches are summed within each stream before ratios and distributions are reported. Noise/protocol/budget conditions are paired. Full SciPy runs first and selective order alternates. Ratios above one favor selective maintenance. Stage and total results are deliberately separate: a faster component is positive engineering evidence even when another component or initialization prevents a whole-pipeline gain.

| Initial noise | Protocol | Requested batch fraction | Selective solver | Feature-stage speedup | Cost-stage speedup | Update-only pipeline speedup | Setup + ten updates speedup |
|---|---|---|---|---|---|---|---|
| 1% | independent | 0.1% | dynamic | 9.25× | 1.68× | 0.79× | 0.46× |
| 1% | independent | 0.1% | scipy | 9.09× | 1.67× | 1.95× | 1.79× |
| 1% | independent | 1.0% | dynamic | 1.73× | 0.52× | 0.16× | 0.16× |
| 1% | independent | 1.0% | scipy | 1.72× | 0.52× | 1.15× | 1.13× |
| 1% | shared_latent | 0.1% | dynamic | 9.43× | 1.72× | 2.16× | 0.77× |
| 1% | shared_latent | 0.1% | scipy | 9.46× | 1.61× | 2.04× | 1.85× |
| 1% | shared_latent | 1.0% | dynamic | 1.71× | 0.54× | 0.38× | 0.34× |
| 1% | shared_latent | 1.0% | scipy | 1.71× | 0.53× | 1.23× | 1.19× |
| 5% | independent | 0.1% | dynamic | 9.26× | 1.71× | 1.27× | 0.53× |
| 5% | independent | 0.1% | scipy | 9.23× | 1.56× | 1.49× | 1.42× |
| 5% | independent | 1.0% | dynamic | 1.71× | 0.53× | 0.27× | 0.21× |
| 5% | independent | 1.0% | scipy | 1.71× | 0.53× | 1.12× | 1.11× |
| 5% | shared_latent | 0.1% | dynamic | 9.05× | 1.73× | 1.42× | 0.54× |
| 5% | shared_latent | 0.1% | scipy | 9.09× | 1.73× | 1.51× | 1.44× |
| 5% | shared_latent | 1.0% | dynamic | 1.71× | 0.53× | 0.33× | 0.24× |
| 5% | shared_latent | 1.0% | scipy | 1.71× | 0.52× | 1.15× | 1.13× |

These are medians of paired stream-total ratios, not ratios of pooled batch means. Aggregate JSON retains IQR/ranges, method-specific initialization, cumulative stage totals and per-step latency/quality. Cost-stage ratios describe the existing dense refresh implementation, including copies and repeated row/column intersections; they are not subquadratic indexing evidence. Feature-stage ratios include support discovery and dirty detection on selective pipelines. All cache arrays/scale persist across steps; normalization remains frozen initially.

Final mean NC after ten steps:

| Initial noise | Protocol | Requested batch fraction | Keep-initial NC | Full / compiled selective NC | Warm selective NC |
|---|---|---|---|---|---|
| 1% | shared_latent | 0.1% | 99.16% | 97.52% | 97.52% |
| 1% | shared_latent | 1.0% | 99.16% | 94.98% | 94.98% |
| 1% | independent | 0.1% | 99.16% | 81.58% | 81.58% |
| 1% | independent | 1.0% | 99.16% | 20.12% | 20.12% |
| 5% | shared_latent | 0.1% | 84.68% | 80.38% | 80.38% |
| 5% | shared_latent | 1.0% | 84.68% | 79.00% | 79.00% |
| 5% | independent | 0.1% | 84.68% | 70.46% | 70.46% |
| 5% | independent | 1.0% | 84.68% | 17.28% | 17.28% |

Exact maintenance adds no feature or assignment-objective approximation, but descriptor minimization still need not improve hidden correspondence. Objective correctness, stage efficiency and identity quality are distinct outcomes. Warm ties may select an equally optimal permutation with different NC.

Paper progress: sustained exact maintenance and component-level improvements now have short-stream evidence. Component improvements count positively even if total setup-inclusive latency loses. Literature novelty, long-stream robustness, other topologies, memory/scaling and parallel CPU decomposition remain unproven. Ten steps are a pilot, not an amortization or break-even guarantee. No adaptive fallback is evaluated; switching to compiled assignment does not automatically restore reusable warm duals.

Decision: at requested 0.1%, feature-stage medians improve 9.05–9.46× across selective methods/conditions; compiled selective achieves 1.42–1.85× setup-inclusive speedup. Warm setup-inclusive medians are 0.46–0.77×, despite useful feature gains and some update-only wins. At 1%, feature-stage gains persist at 1.71–1.73× while cost-stage ratios are only 0.52–0.54×; compiled setup-inclusive totals still improve 1.11–1.19×. Warm totals remain slower. This supports positive component progress and a measured compiled pipeline benefit without a universal warm-solver claim.

Independent-edit streams accumulate observation differences: final NC at 1% batches is 20.12% under 1% initial noise and 17.28% under 5% initial noise. Full recomputation has the same decline as exact selective maintenance, so this is not a cache error. Keep-initial retains its fixed true correspondence; it need not maintain the updated descriptor optimum. Shared-latent streams preserve the observation mask and retain much higher NC. Objective/protocol fitness must remain explicit in any paper claim.

Next address the isolated cost-stage regression using [exact persistent cost maintenance](cost_maintenance_design.md): cached normalized features, disjoint changed-row/changed-column blocks and safe in-place dense updates. Compare with the frozen historical refresh on fresh seeds 50–54, count all work/setup/storage, and require full cost and mapping equality. Then apply [topology robustness](topology_robustness_design.md). Do not hide a stage gain if total latency barely changes, and do not claim that cost optimization improves correspondence quality.

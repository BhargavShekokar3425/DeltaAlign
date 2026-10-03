# E10 findings: exact persistent cost maintenance

Completed 40 ten-step streams, 400 updates and 1600 method observations on fresh seeds 50–54 under frozen E09 BA conditions. All feature, dirty-set, normalized-feature and cost arrays match the full oracle at every step. All 1200 active method results return the same SciPy mapping and objective; maximum objective discrepancy is zero. Forty-one tests cover cache blocks, ties, all/no/one-sided/overlapping changes and repeated graph streams. Historical feature, assignment and refresh kernels/results remain unchanged.

The new `src/cost_cache.py` keeps normalized feature arrays, rescales only dirty rows and refreshes disjoint cost blocks. Changed source rows are updated against all targets; changed target columns are updated only against unchanged source rows. The owned dense matrix persists in place. No selector, approximation, warm-dual transition or new assignment algorithm is introduced.

| Initial noise | Protocol | Requested batch fraction | Cost speedup vs historical refresh | Cost speedup vs full construction | Setup-inclusive speedup vs historical selective | Setup-inclusive speedup vs full |
|---|---|---|---|---|---|---|
| 1% | independent | 0.1% | 1.24× | 1.96× | 1.01× | 1.60× |
| 1% | independent | 1.0% | 1.77× | 0.91× | 1.05× | 1.18× |
| 1% | shared_latent | 0.1% | 1.27× | 2.03× | 1.01× | 1.67× |
| 1% | shared_latent | 1.0% | 1.75× | 0.92× | 1.07× | 1.26× |
| 5% | independent | 0.1% | 1.23× | 1.90× | 1.01× | 1.41× |
| 5% | independent | 1.0% | 1.75× | 0.91× | 1.04× | 1.15× |
| 5% | shared_latent | 0.1% | 1.23× | 2.00× | 1.01× | 1.41× |
| 5% | shared_latent | 1.0% | 1.76× | 0.92× | 1.05× | 1.17× |

Ratios above one favor the new cache. These are medians of paired stream-total ratios across five independent seed bundles per condition, with IQR/ranges retained in aggregate JSON. Conditions and batches are paired/correlated; individual batches are not independent repetitions. Component gains count as positive outcomes even when total latency changes little or regresses. Cost time includes normalization, indexing, distance calculations, block writes and required temporaries. Total time includes real method-specific initialization plus ten updates, feature work and compiled assignment. Full recomputation runs first and selective order alternates. Timings exclude graph generation/applying batches, validation and quality evaluation.

The new method eliminates the historical refresh's ten complete matrix copies per ten-step stream and computes row/column intersections once. Distance temporaries remain; this is not a peak-memory claim. Extra normalized feature arrays occupy 432,000 bytes for two 1K graphs, plus a 216-byte scale copy; descriptor arrays occupy 640,000 bytes and dense costs 8,000,000 bytes. Dense storage remains quadratic. Method-specific initialization timings and computed-cell totals are saved.

Cost and mapping equality ensure quality is unchanged relative to full/historical SciPy. The speedup does not repair hidden correspondence or objective/protocol fitness. Keep-initial and NC/S3 controls are retained for every stream, including independent-edit quality declines. Cached normalization stays fixed to initial scale throughout.

Decision: at requested 0.1%, cost-stage medians improve 1.23–1.27× over historical refresh and 1.90–2.03× over full construction. At 1%, the historical-refresh comparison improves 1.75–1.77×, but full construction still wins slightly (full/new cost ratios 0.91–0.92×). E09's large cost-stage regression is reduced, not completely removed. Setup-inclusive medians improve about 1–7% over historical selective maintenance and 1.41–1.67× over full recomputation at 0.1%, or 1.15–1.26× at 1%. The larger component gain has a modest incremental total effect because assignment remains a major cost.

Paper progress: this adds a validated cost-maintenance component with a modest overall improvement as well. Give cost-stage improvements positive credit independently of total pipeline gain. These are engineering results, not verified literature novelty, large-scale memory efficiency, long-stream robustness or parallel decomposition evidence. Next apply the topology robustness gate on fresh seeds 55–59 with initial-quality/no-update controls and exact stream checks, preserving stage gains and failed regimes.

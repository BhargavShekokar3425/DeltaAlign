# E08 findings: compiled assignment control

Completed 80 reset trials and 320 method observations on fresh seeds 40–44 under frozen E07 conditions. Selective compiled features, dirty sets and costs equal the full oracle exactly; its mapping agrees with full SciPy in every trial. All 80 warm results pass dual certificates and match the optimal objective. Maximum absolute objective difference across warm/compiled selective results is 0. The protocol was written before execution; historical kernels and results are preserved.

| Initial noise | Protocol | Requested update | Dynamic / compiled selective pipeline, median | Full / compiled selective pipeline, median | Compiled selective ms, median |
|---|---|---|---|---|---|
| 1% | independent | 0.01% | 0.63× | 2.00× | 79.2 |
| 1% | independent | 0.10% | 0.85× | 1.86× | 84.5 |
| 1% | independent | 1.00% | 6.52× | 1.14× | 148.6 |
| 1% | independent | 5.00% | 16.37× | 0.92× | 212.5 |
| 1% | shared_latent | 0.01% | 0.37× | 1.98× | 81.6 |
| 1% | shared_latent | 0.10% | 0.91× | 1.78× | 88.1 |
| 1% | shared_latent | 1.00% | 2.52× | 1.19× | 128.0 |
| 1% | shared_latent | 5.00% | 9.01× | 0.88× | 149.4 |
| 5% | independent | 0.01% | 0.79× | 1.52× | 148.5 |
| 5% | independent | 0.10% | 1.04× | 1.46× | 151.5 |
| 5% | independent | 1.00% | 3.94× | 1.11× | 204.7 |
| 5% | independent | 5.00% | 13.17× | 0.93× | 234.0 |
| 5% | shared_latent | 0.01% | 0.48× | 1.51× | 151.6 |
| 5% | shared_latent | 0.10% | 0.89× | 1.45× | 152.0 |
| 5% | shared_latent | 1.00% | 2.33× | 1.13× | 182.4 |
| 5% | shared_latent | 5.00% | 10.26× | 0.91× | 191.9 |

Ratios above one favor compiled selective maintenance. These compare real implementations: a Python/NumPy warm assignment kernel versus compiled SciPy. They do not establish a theoretical superiority of cold assignment. Compiled selective needs descriptor caches and dense costs, but no warm dual state; both selective pipelines count their required clones, support discovery, feature/cost maintenance and solves. The full pipeline runs first and selective order alternates. Five-seed IQR/ranges and raw paired rows are saved. Timing excludes graph generation, edge application and validation; reset trials do not establish production streaming latency.

For two 1K graphs, extra descriptor arrays occupy 640,000 bytes; a dense cost matrix occupies 8,000,000 bytes. Median cache setup is 82.5 ms. Median custom warm initialization is 2191.4 ms versus 108.5 ms for SciPy on the initial matrix. Compiled selective does not require the custom setup. Array bytes omit graph storage, solver workspace and temporaries; no peak-RSS claim is made.

At requested 0.1%, mean quality controls are:

| Initial noise | Protocol | Keep-old NC | Compiled selective NC | Warm selective NC |
|---|---|---|---|---|
| 1% | shared_latent | 98.68% | 97.92% | 97.92% |
| 1% | independent | 98.68% | 95.68% | 95.68% |
| 5% | shared_latent | 82.10% | 81.28% | 81.28% |
| 5% | independent | 82.10% | 79.56% | 79.56% |

Exact descriptor/objective maintenance still does not guarantee better hidden correspondence than keep-old. Warm permutations may differ on equal-cost ties; compiled selective returns the full compiled permutation. The smallest budget is one edit per graph, about 0.033% realized rather than requested 0.01%.

Paper progress: the experiment closes an important attribution gap. Report graph-maintenance gains separately from warm-solver reuse, retain every crossover/regression and avoid a solver-novelty claim. The remaining contribution needs novelty positioning, sustained exact maintenance, broader topology, memory/scaling and eventual CPU decomposition evidence.

Decision: at requested 0.1%, selective compiled beats full recomputation by 1.45–1.86× in every condition; warm selective is faster than compiled selective in three of four conditions. At requested 1%, compiled selective remains 1.11–1.19× faster than full recomputation and is 2.33–6.52× faster than warm selective. At 5%, full recomputation wins in all condition medians. These establish measured regime differences, not a validated adaptive selector.

Next run a short persistent-state stream pilot on fresh seeds 45–49: ten successive batches per stream, requested 0.1% and 1%, both protocols/noise levels. Compare the two selective methods, full compiled recomputation and keep-initial mapping. Count method-specific initialization and cumulative update cost; remove reset-only per-batch clones while retaining real cache/cost work. Validate every step against the full oracle. Record realized budgets, accumulated changes, NC/S3, churn and latency by step. Keep the solver choice fixed per stream; defer adaptive fallback until its dual-state transition cost is addressed. Ten-step evidence is a pilot, not long-stream robustness or an amortization guarantee.

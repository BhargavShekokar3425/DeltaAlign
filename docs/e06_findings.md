# E06 findings: exact assignment reuse

Completed 80 reset trials and 320 method observations on fresh seeds 30–34, 1K BA graphs, two update protocols and two initial noise levels. Configuration, raw rows, initialization, source hashes and the aggregate are saved. All 160 warm/cold reference results passed primal-dual certificates and agreed with SciPy's objective; maximum absolute objective discrepancy was 9.09e-13. Initial reference solves also matched SciPy objectives. Equal-cost ties can give different permutations; objective agreement is the correctness criterion.

The original reference follows the primal-dual repair idea in [CMU-RI-TR-07-27](https://www.cs.cmu.edu/~gertrude/dyn_assign_techreport.pdf). See [the protocol](e06_protocol.md) for implementation differences and provenance. This establishes an existing exact baseline, not algorithmic novelty for DeltaAlign.

| Initial noise | Protocol | Requested update | Exposed rows, mean | Search rows visited, mean | Same-kernel solver speedup, median | SciPy full / dynamic pipeline, median | Dynamic pipeline ms, median |
|---|---|---|---|---|---|---|---|
| 1% | independent | 0.01% | 15.8% | 59.5% | 41.44× | 1.37× | 117.5 |
| 1% | independent | 0.10% | 32.9% | 90.2% | 7.97× | 0.63× | 209.5 |
| 1% | independent | 1.00% | 93.1% | 100.0% | 1.83× | 0.19× | 702.5 |
| 1% | independent | 5.00% | 100.0% | 100.0% | 0.68× | 0.06× | 2638.7 |
| 1% | shared_latent | 0.01% | 14.6% | 39.2% | 52.14× | 1.37× | 110.0 |
| 1% | shared_latent | 0.10% | 23.6% | 77.8% | 16.48× | 0.94× | 151.5 |
| 1% | shared_latent | 1.00% | 80.0% | 93.2% | 5.27× | 0.45× | 317.0 |
| 1% | shared_latent | 5.00% | 99.1% | 99.5% | 0.31× | 0.10× | 1067.5 |
| 5% | independent | 0.01% | 15.6% | 88.1% | 34.99× | 1.39× | 161.0 |
| 5% | independent | 0.10% | 34.2% | 97.6% | 16.55× | 0.85× | 263.6 |
| 5% | independent | 1.00% | 91.7% | 99.9% | 5.00× | 0.32× | 689.7 |
| 5% | independent | 5.00% | 100.0% | 100.0% | 0.86× | 0.07× | 2933.9 |
| 5% | shared_latent | 0.01% | 13.5% | 83.5% | 36.18× | 1.39× | 166.9 |
| 5% | shared_latent | 0.10% | 25.6% | 89.2% | 24.75× | 1.12× | 196.7 |
| 5% | shared_latent | 1.00% | 83.8% | 98.5% | 5.81× | 0.38× | 535.9 |
| 5% | shared_latent | 5.00% | 99.5% | 99.9% | 1.31× | 0.10× | 1864.8 |

Ratios above one favor dynamic repair. Same-kernel speedup compares two implementations using the same Python/NumPy Hungarian kernel. The full pipeline comparison uses compiled SciPy and includes full feature recomputation, dirty detection, dense cache refresh, state cloning and repair; it excludes graph generation, applying edge batches and correctness certificates. It is a graph-to-assignment measurement, not complete streaming latency. Timing order is fixed, and five-seed distributions describe this machine/run rather than universal speedups. IQR and ranges are in the aggregate. No speedup against E05's restricted methods is asserted because E06 initializes its mapping with the custom optimum, which can differ on ties.

At the smallest requested fraction, each graph receives one edit: the realized combined fraction is about 0.033%, not 0.01%. At requested 0.1%, median pipeline ratios range from 0.63× to 1.12×; only the 5%-noise shared-latent condition is faster. Mean search coverage is 77.8–97.6%. At requested 1% and 5%, all condition medians favor compiled full recomputation. Full descriptor recomputation still takes roughly 74 ms at requested 0.1%; selective dense cost refresh takes about 5 ms. Work reduction in the solver therefore does not remove the graph-feature bottleneck.

Dirty cost rows/columns and searched assignment rows are different quantities. Repair can visit rows outside the initially exposed set through competing assignments. Keep-old is still a quality control: minimizing the descriptor objective does not guarantee improved hidden correspondence. The aggregate retains NC, churn and mapping agreement for every method. At requested 0.1%, five-seed mean NC and keep-old objective gaps are:

| Initial noise | Protocol | Keep-old NC | Dynamic NC | SciPy full NC | Keep-old relative objective gap |
|---|---|---|---|---|---|
| 1% | shared_latent | 99.50% | 98.02% | 98.02% | 5.74% |
| 1% | independent | 99.50% | 95.92% | 95.92% | 28.98% |
| 5% | shared_latent | 83.32% | 82.42% | 82.40% | 2.33% |
| 5% | independent | 83.32% | 81.18% | 81.18% | 3.40% |

Initial custom and SciPy mappings agreed on all ten graph pairs in this run. Updated exact optima differed on a few equal-cost ties; the tiny NC differences between exact solvers do not indicate an objective error. The quality comparison confirms E05's concern: exact descriptor minimization can lose true matches relative to keep-old, even while eliminating its objective gap.

The next mechanism must preserve assignment competition and dual feasibility, rather than pre-expanding every candidate owner or relying on row-best margins. See [assignment-aware localization design](assignment_aware_localization.md). First implement exact selective descriptor maintenance against the full descriptor oracle; retain exact cost refresh and dynamic assignment so errors can be isolated. Larger graphs, repeated streams, memory profiling and parallel components remain pending.

Paper progress: closer through a verified, correctness-checked baseline and measured work boundaries. A new compact, efficient graph-aware repair method is still unproven. Assignment reuse by itself is established prior work, and timing gains within a custom solver do not establish an advantage over compiled FullAlign.

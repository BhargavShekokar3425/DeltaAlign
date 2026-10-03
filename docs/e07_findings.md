# E07 findings: exact selective descriptor maintenance

Completed 80 reset trials and 320 method observations on fresh seeds 35–39, 1K BA attachment 3, shared-latent/independent protocols and 1%/5% observation noise. The protocol was written before execution. All feature arrays, actual dirty sets and refreshed cost matrices matched full recomputation exactly. Both dynamic pipelines returned identical permutations in every paired trial. All 160 dynamic results passed global primal-dual certificates and matched SciPy objectives; maximum absolute objective discrepancy was 0.

The new component caches degrees, raw histograms and final features. Endpoint and neighbor dependencies determine first-layer support; only actually changed histograms propagate to the next layer. Complete statistics are recomputed for supported rows to preserve numerical equality. Historical descriptor, normalization and assignment implementations remain unchanged. This demonstrates exact graph-specific maintenance, not a novel assignment algorithm or verified literature novelty.

| Initial noise | Protocol | Requested update | Feature support, mean | Feature speedup, median | Full-feature dynamic / selective pipeline, median | SciPy full / selective pipeline, median | Selective pipeline ms, median |
|---|---|---|---|---|---|---|---|
| 1% | independent | 0.01% | 10.9% | 21.77× | 2.13× | 2.45× | 62.8 |
| 1% | independent | 0.10% | 18.8% | 9.49× | 1.62× | 1.46× | 108.4 |
| 1% | independent | 1.00% | 81.0% | 1.76× | 1.03× | 0.15× | 997.8 |
| 1% | independent | 5.00% | 99.4% | 0.93× | 1.00× | 0.05× | 4143.6 |
| 1% | shared_latent | 0.01% | 10.4% | 19.66× | 3.58× | 5.53× | 28.4 |
| 1% | shared_latent | 0.10% | 16.2% | 12.52× | 2.55× | 3.46× | 43.2 |
| 1% | shared_latent | 1.00% | 83.3% | 1.65× | 1.10× | 0.42× | 378.2 |
| 1% | shared_latent | 5.00% | 99.4% | 0.91× | 1.00× | 0.05× | 2397.8 |
| 5% | independent | 0.01% | 9.3% | 23.38× | 1.81× | 2.45× | 91.4 |
| 5% | independent | 0.10% | 17.8% | 10.09× | 1.37× | 1.29× | 172.9 |
| 5% | independent | 1.00% | 82.8% | 1.64× | 1.04× | 0.26× | 844.0 |
| 5% | independent | 5.00% | 99.1% | 0.93× | 1.00× | 0.05× | 3445.3 |
| 5% | shared_latent | 0.01% | 10.0% | 23.64× | 1.84× | 2.65× | 84.7 |
| 5% | shared_latent | 0.10% | 17.0% | 11.46× | 1.66× | 2.04× | 105.7 |
| 5% | shared_latent | 1.00% | 81.4% | 1.68× | 1.05× | 0.40× | 564.8 |
| 5% | shared_latent | 5.00% | 99.3% | 0.92× | 1.00× | 0.07× | 2668.3 |

Ratios above one favor selective maintenance. The feature ratio includes support discovery, layer maintenance and dirty detection; pipeline totals also count descriptor-cache and assignment-state clones, cost refresh and solver work. The additional descriptor caches occupy 640,000 bytes for two graphs; the dense cost cache alone occupies 8,000,000 bytes. Median extra cache initialization was 80.8 ms. These are array bytes, not peak RSS or all temporary storage.

The smallest requested fraction gives one edit per graph (about 0.033% realized). Both dynamic timings were measured on identical fresh conditions, with their order alternating; full SciPy ran first. Five-seed distributions describe this run, not general speed guarantees. Raw paired rows and aggregate IQR/ranges are saved. Updated-graphs-to-assignment timing excludes graph generation, applying edits and validation. Global certificate scans are validation-only; no operational certificate cost or stream performance claim is made. Cost-rescore counts are unique covered cells; the inherited row/column refresh can compute intersections twice.

At requested 0.1%, quality controls remain essential:

| Initial noise | Protocol | Keep-old NC | Exact selective repair NC | Keep-old relative objective gap |
|---|---|---|---|---|
| 1% | shared_latent | 98.64% | 97.82% | 3.65% |
| 1% | independent | 98.64% | 96.80% | 13.71% |
| 5% | shared_latent | 79.34% | 79.02% | 0.79% |
| 5% | independent | 79.34% | 78.48% | 1.78% |

Exact feature maintenance introduces no additional descriptor or assignment approximation. It also cannot fix the underlying objective's disagreement with hidden correspondence. Keep-old retains its role as a control. Equal-cost SciPy permutations can differ from the two identical dynamic results.

Paper progress: this adds an implemented, validated graph-maintenance component beyond assignment reuse, with measured efficiency and crossover evidence. It does not establish literature novelty, compact assignment search, large-scale memory efficiency, temporal robustness or parallel CPU scaling. Interpret the timing table before choosing the next stage; retain failures and quality controls.

The next missing control is selective features and selective cost refresh followed by compiled SciPy assignment. E07's paired dynamic comparison isolates feature maintenance, but does not show that warm assignment reuse is necessary to obtain its gains. Test that control on fresh seeds 40–44 against selective dynamic repair, full compiled recomputation and keep-old before designing fallback thresholds or moving to streams. A future compiled fallback must account for how reusable dual state is restored; SciPy does not supply this reference's dual potentials.

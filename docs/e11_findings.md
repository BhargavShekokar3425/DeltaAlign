# E11 findings: topology robustness

Completed 120 ten-step streams, 1200 updates and 4800 observations on fresh seeds 55–59. All 3600 active results match full-oracle features, dirty sets, normalized features, costs, SciPy mappings and objectives exactly. All 360 actual no-update controls preserve features/costs/scale/mappings. Forty-two tests pass. Historical generation and E10 maintenance kernels are unchanged. Thirty initial graph-pair controls and graph statistics are saved.

BA attachment 3, ER p=6/(n-1), and WS k=6/rewiring 0.1 have expected/specified mean degree near six; actual density, isolates, components, degree extrema and clustering are retained rather than presumed equal. Hidden correspondence enters generation/evaluation only. Initial alignment quality and descriptor ambiguity are:

| Topology | Initial noise | Full NC, mean | Random NC, mean | Source unique feature fraction, mean | Rows with tied minimum, mean |
|---|---|---|---|---|---|
| BA | 1% | 98.60% | 0.16% | 100.0% | 0.0% |
| BA | 5% | 83.88% | 0.16% | 100.0% | 0.0% |
| ER | 1% | 94.82% | 0.16% | 99.9% | 0.4% |
| ER | 5% | 56.60% | 0.16% | 99.9% | 0.2% |
| WS | 1% | 33.58% | 0.16% | 66.4% | 43.3% |
| WS | 5% | 6.94% | 0.16% | 66.4% | 29.1% |

Feature uniqueness is the number of distinct descriptor rows divided by vertices, not the fraction of vertices whose descriptor occurs only once. Uniqueness and row-minimum ties are descriptor diagnostics, not a complete count of alternative optimal assignments. Initial random S3, target uniqueness, truth row-minimum frequency and graph-statistic distributions are in aggregate JSON. Keep-initial uses the initial full optimum and retains fixed vertex truth; it is a necessary control rather than an updated-objective solver.

| Topology | Noise | Protocol | Requested batch fraction | Feature-stage speedup | Cost-stage speedup | Setup-inclusive total speedup | Final full/selective NC, mean | Keep-initial NC, mean |
|---|---|---|---|---|---|---|---|---|
| BA | 1% | independent | 0.1% | 8.81× | 1.91× | 1.54× | 83.84% | 98.60% |
| BA | 1% | independent | 1.0% | 1.70× | 0.92× | 1.17× | 13.96% | 98.60% |
| BA | 1% | shared_latent | 0.1% | 9.06× | 2.04× | 1.63× | 96.70% | 98.60% |
| BA | 1% | shared_latent | 1.0% | 1.72× | 0.91× | 1.25× | 95.40% | 98.60% |
| BA | 5% | independent | 0.1% | 9.22× | 2.02× | 1.40× | 70.46% | 83.88% |
| BA | 5% | independent | 1.0% | 1.72× | 0.92× | 1.15× | 16.14% | 83.88% |
| BA | 5% | shared_latent | 0.1% | 9.25× | 2.02× | 1.41× | 81.40% | 83.88% |
| BA | 5% | shared_latent | 1.0% | 1.73× | 0.92× | 1.18× | 75.86% | 83.88% |
| ER | 1% | independent | 0.1% | 13.42× | 3.31× | 2.52× | 78.42% | 94.82% |
| ER | 1% | independent | 1.0% | 2.02× | 0.96× | 1.27× | 8.84% | 94.82% |
| ER | 1% | shared_latent | 0.1% | 13.50× | 3.25× | 2.91× | 95.24% | 94.82% |
| ER | 1% | shared_latent | 1.0% | 2.04× | 0.96× | 1.45× | 94.24% | 94.82% |
| ER | 5% | independent | 0.1% | 13.27× | 3.28× | 1.93× | 43.86% | 56.60% |
| ER | 5% | independent | 1.0% | 2.01× | 0.96× | 1.25× | 6.24% | 56.60% |
| ER | 5% | shared_latent | 0.1% | 13.01× | 3.15× | 2.02× | 56.60% | 56.60% |
| ER | 5% | shared_latent | 1.0% | 2.05× | 0.96× | 1.31× | 58.44% | 56.60% |
| WS | 1% | independent | 0.1% | 16.04× | 4.66× | 1.60× | 14.98% | 33.58% |
| WS | 1% | independent | 1.0% | 2.37× | 1.12× | 1.24× | 0.68% | 33.58% |
| WS | 1% | shared_latent | 0.1% | 16.15× | 4.78× | 1.60× | 37.74% | 33.58% |
| WS | 1% | shared_latent | 1.0% | 2.37× | 1.11× | 1.29× | 59.76% | 33.58% |
| WS | 5% | independent | 0.1% | 15.90× | 4.67× | 1.25× | 4.16% | 6.94% |
| WS | 5% | independent | 1.0% | 2.34× | 1.11× | 1.14× | 0.66% | 6.94% |
| WS | 5% | shared_latent | 0.1% | 16.03× | 4.67× | 1.25× | 8.36% | 6.94% |
| WS | 5% | shared_latent | 1.0% | 2.36× | 1.10× | 1.15× | 15.94% | 6.94% |

Ratios above one favor persistent selective maintenance over full recomputation. Stage and total gains are separate positive outcomes: a component gain counts as progress even if total latency loses. Historical-refresh comparison, support/dirty expansion, update-only totals, NC/S3, mask drift and IQR/ranges are saved in the aggregate. These are paired ratios of ten-step stream totals across five seeds per condition, not pooled correlated batches; families/conditions share seed branches. Setup is method-specific; full recomputation runs first and selective order alternates. Generation/applying edits, diagnostics, validation and quality evaluation are excluded from graph-to-assignment ratios. No-update diagnostics are additional correctness work outside the ten-step timing totals.

Exact maintained costs guarantee unchanged compiled alignment behavior, not improved correspondence quality. Independent edits accumulate observation differences while the hidden mapping stays fixed; retain quality failures across all families. Weak initial descriptor discrimination limits alignment-method claims but does not erase a validated exact-maintenance efficiency gain. Do not discard families or tune the descriptor after seeing results.

Decision: feature-stage gains extend beyond BA. At requested 0.1%, median feature speedups are 8.81–9.25× on BA, 13.01–13.50× on ER and 15.90–16.15× on WS. Setup-inclusive totals improve 1.40–1.63×, 1.93–2.91× and 1.25–1.60× respectively. At 1%, feature improvements remain 1.70–2.37× and setup-inclusive totals improve 1.14–1.45× across all families. All 24 condition medians favor the persistent pipeline. Cost maintenance still loses slightly to full cost construction at 1% on BA/ER, while WS cost maintenance wins. Component gains and component regressions remain explicit.

WS fails a strong correspondence-quality gate: initial NC averages 33.58% at 1% noise and 6.94% at 5%, with only 66.4% distinct source feature rows. ER at 5% noise also starts at only 56.60% NC. Some shared-latent streams improve NC relative to keep-initial (WS at 1% noise/1% batches reaches 59.76%), but full recomputation has the same outcome; this is not a selective-method quality advantage. Independent streams severely degrade NC on all families. Maintain the narrow objective-maintenance claim and do not treat initial row-uniqueness/tie diagnostics as a complete explanation or a novelty proof.

Paper progress: the efficiency evidence now generalizes across three tested topologies, with validated component and total gains. Objective-quality robustness is still a material blocker for a stronger alignment-method claim. Novelty remains unverified; this 1K, ten-step synthetic experiment does not establish larger-size memory performance, long-stream robustness or CPU-parallel decomposition. Next run [isolated resource/size profiling](resource_scaling_design.md) on fresh seed 60, counting actual peak RSS and retaining the quality limits. A one-seed profile is a viability gate before replicated scaling, not a new statistical speedup claim.

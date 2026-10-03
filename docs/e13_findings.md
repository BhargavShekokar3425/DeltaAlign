# E13 findings: replicated bounded scaling

Completed 60 sequential fresh-worker runs: 30 paired seed bundles, with five fresh seeds (61–65) per size/topology. All 120 setup/update snapshots agree exactly in features, normalized features, scale, costs, mapping and objective. All planned conditions passed visible resource preflight. First-worker order alternates, balanced across all pairs. Frozen E12 numerical kernels and cost-matrix lifecycle are preserved.

Each cell reports median [Q25, Q75]; minimum–maximum across five paired seeds. Timing ratios are full/persistent; RSS ratios are persistent/full. Three correlated updates are summed within each worker, not treated as independent samples. Total includes actual initialization. RSS is the whole-worker high-water mark including validation and quality; generation and validation are excluded from stage timings.

| Nodes | Topology | Feature ratio | Cost ratio | Update ratio | Setup + updates ratio | RSS ratio | Total wins |
|---|---|---|---|---|---|---|---|---|
| 2,000 | BA | 7.39 [7.39, 7.62]; 6.34–8.16 | 1.76 [1.72, 1.92]; 1.61–2.06 | 1.24 [1.23, 1.24]; 1.22–1.28 | 1.15 [1.15, 1.17]; 1.15–1.19 | 1.08 [1.07, 1.12]; 1.05–1.13 | 5/5 |
| 2,000 | ER | 13.11 [12.86, 14.29]; 12.83–14.47 | 3.01 [2.68, 3.03]; 2.68–3.20 | 2.22 [2.20, 2.24]; 2.01–2.71 | 1.66 [1.65, 1.66]; 1.58–1.84 | 1.03 [1.02, 1.05]; 1.00–1.07 | 5/5 |
| 2,000 | WS | 18.47 [18.15, 18.73]; 17.54–19.06 | 5.05 [4.30, 5.10]; 4.18–5.21 | 1.34 [1.21, 1.34]; 1.18–1.40 | 1.23 [1.15, 1.23]; 1.11–1.29 | 1.02 [1.01, 1.03]; 0.98–1.07 | 5/5 |
| 5,000 | BA | 7.74 [7.44, 7.88]; 6.62–8.01 | 1.84 [1.83, 1.97]; 1.69–1.98 | 1.04 [1.04, 1.06]; 1.03–1.06 | 1.03 [1.02, 1.04]; 1.02–1.04 | 1.17 [1.16, 1.18]; 1.14–1.22 | 5/5 |
| 5,000 | ER | 14.20 [14.10, 14.27]; 13.74–14.56 | 3.64 [3.47, 3.70]; 3.45–4.01 | 1.36 [1.30, 1.36]; 1.15–1.42 | 1.24 [1.21, 1.25]; 1.13–1.28 | 1.14 [1.11, 1.15]; 1.08–1.18 | 5/5 |
| 5,000 | WS | 17.92 [17.69, 18.35]; 17.59–18.39 | 5.42 [5.35, 5.45]; 5.32–5.57 | 1.04 [1.03, 1.05]; 1.02–1.05 | 1.03 [1.02, 1.03]; 1.01–1.04 | 1.06 [1.05, 1.07]; 1.03–1.09 | 5/5 |

All seed observations, stage seconds, quality controls and RSS MiB are retained in the aggregate. Boxplots show seed distributions and individual pairs; they are not confidence intervals. These are independent graph/edit seeds on one machine, not repeated executions of identical jobs. Near-one total ratios must be interpreted with that timing limitation. Resource gates inspect visible limits only.

Component gains are positive evidence even when total gains are small: the compiled assignment stage still dominates at larger sizes. Exact matching agreement demonstrates objective maintenance, not better correspondence accuracy. Maintained memory overhead and quadratic dense storage remain limitations. Noise, update budget and three-step stream length were deliberately fixed; no broad scaling or long-stream claim follows.

Decision: across all 30 paired bundles, observed setup-inclusive ratios favor maintenance. At 5K, median feature gains are 7.74× BA, 14.20× ER and 17.92× WS; cost gains are 1.84×, 3.64× and 5.42×. Setup-inclusive medians are 1.03×, 1.24× and 1.03×, with respective ranges 1.02–1.04×, 1.13–1.28× and 1.01–1.04×. Five seed bundles strengthen the component result, but the small BA/WS total effects still need repeated execution to separate timing variability.

Median 5K persistent peak RSS is 354.2 MiB BA, 343.4 MiB ER and 315.8 MiB WS; paired persistent/full median ratios are 1.17, 1.14 and 1.06. Dense assignment consumes about 97.8–97.9% of maintained BA update stages, 93.3–97.7% ER and 99.4–99.5% WS. Optimizing descriptor/cost work alone therefore has limited remaining total-latency headroom at this size.

Median initial/final NC at 5K is 96.36%/93.00% BA, 88.12%/87.86% ER and 15.64%/15.26% WS. These diagnostics preserve the objective-quality limitation; they do not show a maintenance accuracy benefit. Forty-four tests pass, including fresh-seed worker equality; all frozen E12 source hashes remain unchanged.

Paper progress: closer through replicated exact component efficiency and bounded 5K viability. This supports a component-focused experimental result even where total benefits are small and memory rises. It does not establish novelty, useful WS correspondence, broad noise/budget robustness, long-stream scaling or certified CPU decomposition. Next execute the [primary-source contribution audit](post_e13_research_gate.md) before expanding compute or claiming a new assignment method.

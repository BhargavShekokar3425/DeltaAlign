# E15 findings: attribution beyond conservative locality

Completed all 120 sequential fresh workers across 30 paired streams on fresh seeds 66–70, 1K BA/ER/WS, 1% initial noise, two update budgets and ten shared-latent steps. All 990 non-full-versus-full setup/update snapshots have identical features, normalized features, scales, costs, mappings and objectives. There are 300 unique graph-update scenarios and 1,200 method-update observations. All inspected resource gates passed. Forty-six tests pass, including controls for no changes, isolates, bin crossings, degree-preserving edits and consecutive mixed updates. Historical kernels remain unchanged.

Each table cell is median [Q25, Q75]; range across five paired seed streams. Ten correlated steps are summed within each worker. Feature/cost ratios compare conservative control time to refined time; ratios above one favor refined maintenance. Work ratios compare conservative to refined row/entry counts. Total ratios compare full to refined setup plus ten updates.

| Topology | Budget | Feature control/refined | Cost control/refined | Second-layer work ratio | Cost-entry work ratio | Full/refined total |
|---|---|---|---|---|---|---|
| BA | 0.1% | 1.41 [1.35, 1.42]; 1.26–1.47 | 1.61 [1.45, 1.68]; 1.34–1.92 | 1.96 [1.84, 2.05]; 1.58–2.34 | 1.76 [1.61, 1.80]; 1.45–1.99 | 1.67 [1.64, 1.68]; 1.60–1.71 |
| BA | 1.0% | 1.05 [1.05, 1.06]; 1.05–1.07 | 0.99 [0.99, 1.00]; 0.96–1.01 | 1.21 [1.21, 1.21]; 1.19–1.21 | 1.05 [1.05, 1.05]; 1.04–1.05 | 1.25 [1.25, 1.25]; 1.24–1.27 |
| ER | 0.1% | 1.31 [1.31, 1.34]; 1.25–1.35 | 1.65 [1.59, 1.72]; 1.52–1.79 | 1.85 [1.85, 1.95]; 1.67–2.07 | 1.78 [1.77, 1.85]; 1.60–1.96 | 2.85 [2.68, 3.24]; 2.56–3.35 |
| ER | 1.0% | 1.09 [1.09, 1.10]; 1.08–1.10 | 1.04 [1.04, 1.06]; 1.02–1.08 | 1.28 [1.25, 1.29]; 1.22–1.29 | 1.10 [1.09, 1.11]; 1.08–1.11 | 1.44 [1.44, 1.50]; 1.44–1.52 |
| WS | 0.1% | 1.12 [1.11, 1.13]; 1.09–1.14 | 1.43 [1.36, 1.46]; 1.35–1.52 | 1.45 [1.37, 1.45]; 1.33–1.54 | 1.43 [1.36, 1.43]; 1.31–1.51 | 1.67 [1.57, 1.75]; 1.52–2.02 |
| WS | 1.0% | 1.08 [1.07, 1.10]; 1.04–1.12 | 1.11 [1.10, 1.14]; 1.08–1.16 | 1.29 [1.28, 1.29]; 1.28–1.30 | 1.17 [1.17, 1.17]; 1.17–1.18 | 1.35 [1.30, 1.36]; 1.23–1.38 |

The aggregate retains every seed, all methods' update/setup-inclusive ratios, RSS, stage seconds, support counts, normalized-row counts, cost-entry counts and initial/final NC/EC/S3. Raw per-step records retain order and validation fingerprints. The second-layer plot shows work and time together; it does not infer timing from row counts. Extra conservative-cost support construction is recorded separately and included in pipeline time; its cost-plus-support ratio is also retained. Refined workers are not charged for unneeded conservative diagnostics.

This isolates implementation controls using the same features, frozen normalization, cache initialization and compiled solver. Conservative feature maintenance uses the same first-layer numerical operations and recomputes a safe second-layer superset; conservative cost maintenance refreshes a safe dirty superset. Neither control is an InkStream/RIPPLE++ reproduction. All workers use E13's dense-matrix lifecycle, buffer fingerprints and whole-worker peak RSS scope. Timings exclude graph generation and validation.

The config's `preregistered_not_run` status is retained as the frozen preregistration record; the execution status is completed in this aggregate and memo. No unfavorable seed/condition was excluded. These are seed replications on one machine, not repeated fixed-job timings. Small total effects remain timing-inconclusive. Identical mappings imply no accuracy advantage; weak WS quality and dense storage remain limitations. No 10K, real-data, long-stream or CPU parallelism claim follows.

Decision: refined feature maintenance is faster than conservative feature maintenance in all 30 seed streams. At 0.1%, median feature-stage gains are 1.41× BA, 1.31× ER and 1.12× WS; cost-stage gains over conservative dirty supersets are 1.61×, 1.65× and 1.43×. Conservative controls recompute 1.45–1.96× as many second-layer rows and 1.43–1.78× as many cost entries at these condition medians. These are validated component improvements beyond simpler locality and count as better outcomes.

At 1%, feature medians still favor refined maintenance by 1.05–1.09×. Cost medians are 0.99× BA, 1.04× ER and 1.11× WS. BA costs therefore do not improve despite a 1.05× cost-entry work ratio. Including conservative support construction gives a BA cost-plus-support ratio of 1.08×, but that is a different measurement, not a bare-cost win. This counterexample prevents equating avoided entries with lower measured latency.

Most total savings come from locality shared by all maintained methods. Conservative/refined setup-inclusive median ratios range 1.004–1.044 for feature controls and 1.006–1.053 for cost controls; these small differences need fixed-job repetition for robust timing claims. Refined/full setup-inclusive medians range 1.25–2.85×. All maintained methods preserve identical quality, and memory outcomes must remain separate from time benefits.

Paper progress: closer through an explicit attribution control showing consistent refined feature benefits and sparse cost benefits. This strengthens a component-focused empirical result; it does not overcome E14's prior-art overlap or establish a new propagation algorithm. Weak WS correspondence, dense memory, real-topology/longer-stream evidence and certified CPU repair remain gaps. Next isolate repeated-execution variability for E13's near-one 5K BA/WS totals using the fixed-job [E16 timing protocol](e16_protocol.md). Do not use a 1K component gain to claim a robust 5K whole-pipeline gain.

## All maintained methods versus full

Each cell is a paired-seed median. Ratios above one favor maintenance for latency and indicate more memory for RSS.

| Topology | Budget | Method | Update-only full/method | Setup + updates full/method | Method/full peak RSS |
|---|---|---|---|---|---|
| BA | 0.1% | persistent_scipy | 1.801 | 1.667 | 1.011 |
| BA | 0.1% | conservative_features | 1.741 | 1.619 | 1.010 |
| BA | 0.1% | conservative_costs | 1.731 | 1.608 | 1.038 |
| BA | 1.0% | persistent_scipy | 1.292 | 1.245 | 1.107 |
| BA | 1.0% | conservative_features | 1.270 | 1.228 | 1.103 |
| BA | 1.0% | conservative_costs | 1.287 | 1.241 | 1.116 |
| ER | 0.1% | persistent_scipy | 3.617 | 2.851 | 0.996 |
| ER | 0.1% | conservative_features | 3.433 | 2.753 | 1.010 |
| ER | 0.1% | conservative_costs | 3.393 | 2.726 | 1.036 |
| ER | 1.0% | persistent_scipy | 1.528 | 1.445 | 1.031 |
| ER | 1.0% | conservative_features | 1.457 | 1.385 | 1.040 |
| ER | 1.0% | conservative_costs | 1.509 | 1.430 | 1.076 |
| WS | 0.1% | persistent_scipy | 1.809 | 1.675 | 1.034 |
| WS | 0.1% | conservative_features | 1.797 | 1.665 | 1.038 |
| WS | 0.1% | conservative_costs | 1.796 | 1.666 | 1.011 |
| WS | 1.0% | persistent_scipy | 1.426 | 1.353 | 1.107 |
| WS | 1.0% | conservative_features | 1.386 | 1.326 | 1.081 |
| WS | 1.0% | conservative_costs | 1.397 | 1.329 | 1.085 |

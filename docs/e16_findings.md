# E16 findings: repeated fixed-job timing

Completed 60 sequential fresh workers, three paired execution rounds within each of ten fixed 5K BA/WS seed jobs (61–65). All 120 paired setup/update snapshots match features, normalized features, scales, costs, mapping and objective, and every worker matches the saved E13 job fingerprints/objectives. All three round-level visible resource gates passed. Forty-seven tests pass, including rejection of historical fingerprint/objective/step drift. Historical kernels remain unchanged.

The E13 workers, initialization, graph/edit construction and cost-matrix lifecycle are frozen. Each total counts actual setup plus three shared-latent 0.1% updates under 1% initial noise. Stage timing excludes graph generation and validation; whole-worker RSS includes them. Method-first order is balanced across all 30 pairs; timestamps, hardware/software, inherited thread environment, hashes and headroom are saved. No first round, slower repeat or seed was discarded. Config status remains the frozen preregistration label; execution completion is recorded separately.

| Topology | Seed | Paired total ratios, rounds 1/2/3 | Median ratio | Full seconds range | Persistent seconds range | Observed wins |
|---|---|---|---|---|---|---|
| BA | 61 | 1.0340, 1.0265, 1.0322 | 1.0322 | 39.893–40.094 | 38.709–38.864 | 3/3 |
| BA | 62 | 1.0359, 1.0590, 1.0395 | 1.0395 | 34.040–34.528 | 32.603–32.894 | 3/3 |
| BA | 63 | 1.0400, 1.0391, 1.0358 | 1.0391 | 35.542–35.833 | 34.299–34.486 | 3/3 |
| BA | 64 | 1.0323, 1.0309, 1.0473 | 1.0323 | 36.182–36.733 | 35.075–35.276 | 3/3 |
| BA | 65 | 1.0477, 1.0345, 1.0414 | 1.0414 | 35.186–35.428 | 33.789–34.039 | 3/3 |
| WS | 61 | 1.0341, 1.0428, 1.0279 | 1.0341 | 49.268–49.843 | 47.799–47.994 | 3/3 |
| WS | 62 | 1.0210, 1.0225, 1.0317 | 1.0225 | 59.265–60.517 | 57.963–58.660 | 3/3 |
| WS | 63 | 0.9637, 1.0297, 1.0320 | 1.0297 | 46.413–46.743 | 45.296–48.161 | 2/3 |
| WS | 64 | 1.0477, 1.0417, 1.0367 | 1.0417 | 46.846–47.094 | 44.928–45.208 | 3/3 |
| WS | 65 | 1.0251, 1.0426, 1.0345 | 1.0345 | 58.952–59.876 | 57.048–57.879 | 3/3 |

## Across five per-seed medians

- **BA**: feature ratio 7.7942 [Q25 7.7671, Q75 7.8693]; range 6.5281–8.0117; cost ratio 1.8589 [Q25 1.8541, Q75 1.9823]; range 1.6936–1.9901; update-only ratio 1.0530 [Q25 1.0495, Q75 1.0545]; range 1.0399–1.0566; setup-inclusive ratio 1.0391 [Q25 1.0323, Q75 1.0395]; range 1.0322–1.0414; persistent/full RSS ratio 1.1816 [Q25 1.1759, Q75 1.2080]; range 1.1519–1.2257. Total directions favor maintenance in 15/15 executions; 0/5 jobs have overlapping full/persistent total-time ranges across rounds.
- **WS**: feature ratio 17.9572 [Q25 17.9223, Q75 18.1479]; range 17.7679–18.4076; cost ratio 5.3708 [Q25 5.3277, Q75 5.4303]; range 5.3167–5.4566; update-only ratio 1.0455 [Q25 1.0391, Q75 1.0499]; range 1.0314–1.0537; setup-inclusive ratio 1.0341 [Q25 1.0297, Q75 1.0345]; range 1.0225–1.0417; persistent/full RSS ratio 1.0578 [Q25 1.0361, Q75 1.0703]; range 1.0349–1.0733. Total directions favor maintenance in 14/15 executions; 1/5 jobs have overlapping full/persistent total-time ranges across rounds.

Each seed's three paired ratios are summarized first, then the five seed medians are summarized by topology. Fifteen executions per topology are not fifteen independent graph/edit seeds. The aggregate retains all raw stage/setup/update seconds, within-job ranges, RSS, quality and order descriptives. Box/point summaries are descriptive, not confidence intervals or significance tests. Historical E13 measurements are context, not a fourth repeat.

Repeated timing evidence is workload/machine-specific and does not establish algorithm novelty or useful WS correspondence. Component improvements count positively regardless of the total outcome. Larger noise/budgets, long streams, real topology and certified CPU decomposition remain untested here. Dense quadratic storage and higher maintained memory remain limitations.

## Decision and paper progress

BA's across-seed median total ratio is 1.0391×; every execution favors maintenance, and each job's observed full/persistent time ranges are separated. Full relative within-job timing ranges are 0.50–1.51%, maintained ranges 0.40–0.89%. This supports a small repeatable setup-inclusive saving for these fixed BA jobs on this machine, not broad scalability or a statistical guarantee.

WS's across-seed median total ratio is 1.0341×, but seed 63 reverses direction in round 1 (0.9637×) and its maintained timing range spans 6.31%. The other four WS jobs favor maintenance throughout; 14/15 WS executions favor it overall. Thus median savings are positive and generally consistent, while a uniformly robust whole-pipeline WS win remains unsupported. No repeat is discarded, and no extra repetitions were added after seeing the reversal.

Component gains persist under repetition: BA feature/cost median ratios are 7.79×/1.86× and WS 17.96×/5.37×. These remain positive outcomes even where total timing is variable. Median persistent/full peak-RSS ratios are 1.182 BA and 1.058 WS, approximately 18% and 6% more memory. All mappings and quality remain E13's; no new correspondence-quality benefit or graph-seed robustness is claimed.

Order descriptives favor maintenance at their medians for either first method: BA 1.0379× full-first / 1.0359× maintained-first; WS 1.0367× / 1.0300×. They are descriptive execution groups, not independent-seed significance tests or proof that order has no effect.

Paper progress is positive through repeated component efficiency, a modest consistent BA total result and honest calibration of WS variability. The work is closer to a defensible empirical component paper; E14 novelty overlap, weak WS quality, quadratic dense memory and missing real-topology/longer-stream evidence remain. More synthetic repetitions are not the next priority. Execute the [bounded real-topology provenance and initial-quality gate](real_topology_gate.md): verify ingestion/projection of one real topology, then freeze a small matching/maintenance pilot. Do not expand to 10K, claim natural correspondence from synthetic permutations, or start parallel assignment without a certificate.

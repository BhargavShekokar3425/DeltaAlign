# E12 findings: resource and size viability

Completed 18 sequential fresh-worker runs across 9 paired size/topology conditions on fresh seed 60. Sizes completed: [1000, 2000, 5000]. All 36 paired setup/update snapshots have identical feature, normalized-feature, scale, cost and mapping fingerprints and objectives. Forty-three tests pass, including small-instance fingerprint agreement and baseline cost release. This is one run per condition: no replicated scaling, statistical speedup or long-stream claim.

The final run uses corrected preflight inspection of visible cgroup session/ancestor limits, available memory and address-space soft limits; decisions and estimates are saved. A preliminary partial run was discarded when this inspection was expanded. Pre-existing topology/size/seed/update settings were unchanged. A 5K cost matrix alone is 200,000,000 bytes. Headroom estimation is conservative but cannot reveal hidden resource constraints.

| Nodes | Topology | Feature-stage speedup | Cost-stage speedup | Setup + three updates speedup | Full peak RSS MiB | Persistent peak RSS MiB | Final NC |
|---|---|---|---|---|---|---|---|
| 1,000 | BA | 9.01× | 2.14× | 1.59× | 89.8 | 96.6 | 99.50% |
| 1,000 | ER | 15.34× | 3.99× | 2.33× | 88.2 | 97.8 | 96.60% |
| 1,000 | WS | 17.00× | 5.36× | 1.36× | 96.6 | 97.7 | 40.90% |
| 2,000 | BA | 7.09× | 1.75× | 1.14× | 125.3 | 139.1 | 97.70% |
| 2,000 | ER | 13.10× | 2.78× | 1.60× | 125.5 | 131.4 | 92.10% |
| 2,000 | WS | 19.05× | 4.79× | 1.16× | 126.1 | 128.1 | 27.20% |
| 5,000 | BA | 6.52× | 1.98× | 1.03× | 302.6 | 349.3 | 93.06% |
| 5,000 | ER | 13.05× | 3.34× | 1.18× | 299.7 | 345.0 | 88.00% |
| 5,000 | WS | 18.53× | 5.45× | 1.03× | 302.7 | 318.4 | 13.94% |

Stage ratios sum the three correlated updates within each worker; setup-inclusive ratios additionally count each method's actual initialization. Ratios above one favor maintenance for timings. RSS is the whole fresh-worker high-water mark, including imports, graph generation, setup, updates, fingerprint validation and quality evaluation. The RSS ratio in the aggregate is persistent/full, so values above one indicate more memory. Timing excludes generation and validation. Array storage and OS peak RSS are separate measurements.

Full recomputation discards each old dense matrix when no longer needed; persistent costs remain owned in place. This avoids an artificial baseline memory penalty. Contiguous-buffer fingerprints avoid another dense validation copy, while normalized-feature validation arrays and hashing/quality work still contribute to worker RSS. Both methods use the same frozen numerical kernels and deterministic graph/edit generation. No full oracle and maintained matrix coexist in a measured worker.

Component gains count as positive progress even if assignment limits total latency or persistent temporaries increase peak memory. Dense storage remains quadratic and solver scaling can dominate. Initial/final NC are diagnostic controls, not an accuracy advantage: identical mappings imply identical quality. E11's weak WS/high-noise quality and independent-stream decline remain limits.

Decision: 5K completed on all families. In this profile, feature-stage speedups are 6.52× BA, 13.05× ER and 18.53× WS; cost-stage speedups are 1.98×, 3.34× and 5.45×. Setup-inclusive ratios are only 1.032× BA, 1.185× ER and 1.032× WS because assignment dominates. Persistent peak RSS is 349.3/345.0/318.4 MiB versus full 302.6/299.7/302.7 MiB: approximately 5.2–15.4% more memory. Eliminating historical refresh copies does not imply lower memory than a full method that releases obsolete costs.

Paper progress: size viability and component gains are positive outcomes even with small total gains and higher peak RSS. A viable 5K run is not robust scaling evidence. Novelty, replicated larger-size timings, longer streams and certified parallel decomposition remain pending; initial WS quality at 5K is only 12.94% in this seed. Next follow the [bounded replicated scaling design](replicated_scaling_design.md): fresh seeds 61–65, 2K/5K and frozen three-update conditions, alternating method order. Preserve exact fingerprints and stage/RSS tradeoffs rather than extrapolate this single seed.

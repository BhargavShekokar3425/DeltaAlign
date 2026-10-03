# Descriptor revision findings

Five seed bundles, n=1,000 BA graphs, attachment 3, 1% mixed target noise. Graph/permutation/noise/update seeds and trial resets match the original experiment. Costs remain normalized squared Euclidean with the initial scale frozen. No candidates, stability penalty, repair, or ground-truth features were added.

| Descriptor | Initial NC | One-edit mean churn | One-edit churn range | 0.1% mean churn |
|---|---|---|---|---|
| basic | 68.28% | 7.30% | 2.20%–12.80% | 14.86% |
| degree_hist | 81.00% | 1.76% | 0.40%–3.70% | 8.56% |
| two_hop_hist | 99.06% | 0.34% | 0.00%–1.20% | 3.10% |

The stronger feature adds fixed-bin neighbor-degree counts, then a second-hop neighbor average of those counts, both log1p transformed. It uses structural information only. The first histogram depends on radius 1 around edited endpoints; the second depends on radius 2. Larger structural support increases the feature-update work required by a future incremental implementation.

| Descriptor | Mean noiseless NC | Unique descriptor count range |
|---|---|---|
| basic | 92.58% | 921–941 |
| degree_hist | 93.12% | 926–947 |
| two_hop_hist | 100.00% | 1000–1000 |

## Detection gate

| Requested update | Radius | Mean RF | Recall mean (nonempty trials) | Nonempty trials |
|---|---|---|---|---|
| 0.01% | 0 | 0.20% | 16.67% | 3/5 |
| 0.01% | 1 | 0.90% | 33.33% | 3/5 |
| 0.01% | 2 | 12.96% | 72.22% | 3/5 |
| 0.01% | 3 | 66.18% | 80.56% | 3/5 |
| 0.10% | 0 | 1.18% | 4.46% | 4/5 |
| 0.10% | 1 | 8.66% | 23.94% | 4/5 |
| 0.10% | 2 | 58.70% | 71.64% | 4/5 |
| 0.10% | 3 | 99.02% | 100.00% | 4/5 |

## Missed-change diagnosis

For 1 edit(s), across all seeds: 17 mapping changes; 10 lie outside radius 2; 10 have unchanged source descriptors. Changed-target ownership and assignment competition can therefore require movement beyond descriptor-update support. This is evidence of assignment coupling, not proof that a particular candidate detector will recover them.
For 6 edit(s), across all seeds: 155 mapping changes; 59 lie outside radius 2; 76 have unchanged source descriptors. Changed-target ownership and assignment competition can therefore require movement beyond descriptor-update support. This is evidence of assignment coupling, not proof that a particular candidate detector will recover them.

## Decision and next task

Retain two_hop_hist as the revised diagnostic baseline: quality and one-edit locality improve substantially in this controlled setting. The fixed-radius detection gate still fails to capture nearly all changes with a small region. Next implement candidate-dependency detection and ownership closure as a detection-only experiment at 1K, validated against full candidate refresh. Preserve old matches and explicitly handle new candidate entrants. Measure recall, RF, and closure growth before building repair or expanding to 5K/10K.

These results are limited to five BA seeds and one noise condition. Fixed bins were specified before these runs, but the descriptor selection is based on this development data; subsequent validation needs independent seeds/topologies. Exact FRA can be sensitive to remaining equivalent optima. No-update determinism and permutation-equivariance checks pass. All prior raw files are preserved.

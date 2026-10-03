# Topology robustness gate after cost maintenance

E07/E08 isolate descriptor maintenance from assignment reuse; E09 tests persistence and setup costs. First address E09's measured cost-stage regression via [the cost-maintenance design](cost_maintenance_design.md), then apply this gate. Results remain specific to BA graphs at 1K nodes. A component-level improvement is useful evidence in its own right, but a graph-alignment paper still needs a clear account of when the objective and maintenance mechanism are useful.

Use fresh seeds 55–59 and three fixed graph families: a BA attachment-3 anchor; ER with `p=6/(n-1)`; WS with even `k=6` and rewiring probability `0.1`, all at `n=1000`. These give comparable expected/specified mean degree near six, not identical edge counts or connectivity. Record actual degree/edge statistics, isolated vertices and components. Use the existing fixed hidden permutation and valid mixed observation-noise construction, preserving truth exclusively for generation/evaluation. Add a separate generator rather than changing historical graph generation.

First save initial quality and no-update controls. Compare the frozen two-hop descriptor optimum with keep-initial/random mappings using NC/S3, uniqueness and tie indicators. Do not tune descriptors or remove difficult topologies after seeing quality. Weak alignment quality limits an alignment claim even if exact feature maintenance is fast; report the feature-maintenance result separately.

Then reuse E09's ten-step protocol, frozen normalization, noise levels, requested 0.1%/1% budgets and shared-latent/independent updates. Compare persistent normalized-cost + selective-feature maintenance + compiled SciPy, the historical-cost selective reference, full recomputation + SciPy and keep-initial. This preserves cost-stage attribution as topology changes. Retain compiled selective as the operational reference because E09 supplies initialization-inclusive evidence; broad warm-solver runs are not required for this topology gate. No adaptive solver switching or new parameter sweep.

Require feature/dirty-set/cost equality and identical SciPy mappings at every step. Report stage-total feature and cost speedups, setup-inclusive total latency, support expansion, quality and churn by topology, with five seed-stream observations per condition. Count real initialization and necessary dense copies. Array bytes are not peak RSS; report both only if measured. Keep paired timing distributions and any regression.

This gate can establish whether graph-maintenance benefits survive changes in degree distribution and clustering. It does not prove novelty, long-stream robustness, scale, sparse cost indexing or independent parallel repair. Those remain separate work; verify relevant literature before writing a novelty claim.


## Completed E11 and next gate

This gate is complete; see [E11 findings](e11_findings.md). All tested topology conditions show setup-inclusive median gains and exact numerical/mapping agreement. WS/high-noise initial correspondence quality is weak and remains a material limit. Next follow [isolated resource/size profiling](resource_scaling_design.md) before a broad larger-size benchmark, preserving component outcomes and quality controls.

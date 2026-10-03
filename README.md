# DeltaAlign

A research prototype testing whether sparse edge updates induce localized changes in global network alignment. See PLAN.md and docs/e00_protocol.md.

Install dependencies with `python3 -m pip install -e .` in your environment. Run checks with `python3 -m unittest discover -s tests`. Run the locality diagnostic with `python3 -m experiments.e00_locality --nodes 1000`. The full configured matrix is `python3 -m experiments.e00_locality`; review the baseline gate before increasing scale.

Results are JSONL rows per radius with a configuration/runtime metadata sidecar. Ground truth is used only in evaluation. No incremental repair implementation or speedup claim is present yet.

Reproduce original noiseless controls with `python3 -m experiments.e00_controls`. Install plotting dependencies with `python3 -m pip install -e '.[plots]'`, then regenerate the original findings and figure with `MPLCONFIGDIR=/tmp/deltaalign-matplotlib python3 -m experiments.summarize`. Historical baseline findings are in `docs/e00_findings.md`.

The descriptor revision is complete; see `docs/e00_descriptor_findings.md`. Reproduce both variants with:

```bash
python3 -m experiments.e00_locality --config configs/e00_degree_hist.json --output results/raw/e00_degree_hist_1k.jsonl
python3 -m experiments.e00_locality --config configs/e00_two_hop_hist.json --output results/raw/e00_two_hop_hist_1k.jsonl
MPLCONFIGDIR=/tmp/deltaalign-matplotlib python3 -m experiments.e00_descriptor_comparison
```

The two-hop descriptor improves baseline quality, but fixed-radius detection remains insufficient. Candidate-dependency detection and ownership closure have now been evaluated; local repair and larger-scale runs remain pending.

Candidate maintenance and closure detection are implemented in `src/candidates.py` and `src/conflict_closure.py`. Run the development/holdout, source/target/both experiment with:

```bash
python3 -m experiments.e01_detection
MPLCONFIGDIR=/tmp/deltaalign-matplotlib python3 -m experiments.summarize_detection
```

See `docs/e01_protocol.md` for the scope: cached dense costs, full descriptor oracle, exact candidate-refresh checks, and detection only. These measurements are not incremental repair speedups.

E01 results are in `docs/e01_findings.md`: unconditional candidate closure achieves high recall by including most of the graph. This motivated the completed margin-pruning and confidence-seed experiment below.

The pruning experiment is complete; see `docs/e02_findings.md`. Reproduce its staged development and frozen-policy validation with:

```bash
python3 -m experiments.e02_pruning --stage development
python3 -m experiments.e02_pruning --stage select
python3 -m experiments.e02_pruning --stage validation
MPLCONFIGDIR=/tmp/deltaalign-matplotlib python3 -m experiments.summarize_pruning
```

Selection stores source/config/result hashes before validation. No policy passed the recovery gate: compact regions miss mapping changes and prune many of their full-solution targets. This motivated the completed restricted-solve quality diagnostic below.

The restricted-solve quality diagnostic is complete. Reproduce it, its normalization audit, and its report with:

```bash
python3 -m experiments.e03_repair_quality
python3 -m experiments.e03_normalization_audit
MPLCONFIGDIR=/tmp/deltaalign-matplotlib python3 -m experiments.summarize_repair_quality
```

See `docs/e03_findings.md` and `docs/PAPER_READINESS.md`. The compact dense solve improves objective fidelity relative to pruned repair, but the combined guide remains unmet. Initially constant bins can dominate stress objectives under the inherited scale floor; the next task is a documented normalization correction and objective review against keep-old. Solver-only timings are not speedup claims. Future experiment reports will include paper readiness.

The normalization correction and paired evaluation are complete. For new alignment work, use `src.normalized_align.full_align`, which defaults to unit scaling for initially constant dimensions and accepts a frozen scale for updates. `src.full_align.full_align` retains the historical normalization for reproducibility; earlier experiment outputs are preserved.

```bash
python3 -m experiments.e04_normalization --mode legacy
python3 -m experiments.e04_normalization --mode corrected
MPLCONFIGDIR=/tmp/deltaalign-matplotlib python3 -m experiments.summarize_normalization
```

See `docs/e04_findings.md`: the correction removes extreme stress objectives, but all paired sparse cases are unchanged and compact-quality guides still fail. Next compare shared-latent graph evolution with independent observation edits under frozen corrected normalization and retain keep-old. Paper-readiness reporting is in `docs/PAPER_READINESS.md`.

The update-protocol review is complete:

```bash
python3 -m experiments.e05_protocol_review
MPLCONFIGDIR=/tmp/deltaalign-matplotlib python3 -m experiments.summarize_protocol_review
```

See `docs/e05_findings.md`: low-noise shared evolution admits compact low-gap repair, but keep-old is already highly competitive. Higher noise exposes fidelity failures and objective/truth disagreement. Next verify and evaluate a compatible dynamic-assignment reference before redesigning localization. All earlier results remain preserved; paper readiness is updated after each experiment.


The exact dynamic-assignment reference and benchmark are complete:

```bash
python3 -m experiments.e06_dynamic_assignment
MPLCONFIGDIR=/tmp/deltaalign-matplotlib python3 -m experiments.summarize_dynamic_assignment
python3 -m unittest discover -s tests -v
```

See [E06 findings](docs/e06_findings.md): 80 fresh-seed reset trials, 160 certified exact reference results, and separate solver/pipeline timing. Reuse helps at the smallest update budget, but most larger conditions lose to compiled FullAlign. Assignment search often spreads widely, and exact descriptor minimization still need not improve hidden-truth correspondence. The [next design](docs/assignment_aware_localization.md) targets exact selective descriptor maintenance. [Paper readiness](docs/PAPER_READINESS.md) distinguishes the verified baseline from an unproven new contribution.


Exact selective descriptor maintenance is implemented and evaluated:

```bash
python3 -m experiments.e07_selective_descriptors
MPLCONFIGDIR=/tmp/deltaalign-matplotlib python3 -m experiments.summarize_selective_descriptors
python3 -m unittest discover -s tests -v
```

See [E07 findings](docs/e07_findings.md): full-oracle feature/cost equality and identical paired dynamic mappings across 80 fresh-seed trials. At requested 0.1% updates, selective descriptor maintenance is 9.49–12.52× faster and the graph-to-assignment pipeline beats compiled FullAlign by 1.29–3.46× across all four conditions. At 1%/5%, compiled FullAlign still wins. Cache initialization and copies are recorded separately/in pipeline totals as specified in [the protocol](docs/e07_protocol.md). This is exact objective maintenance; correspondence accuracy is not guaranteed. Next compare selective maintenance with compiled SciPy assignment to separate graph savings from warm solver reuse. [Paper readiness](docs/PAPER_READINESS.md) records progress and remaining evidence.


The compiled-assignment control is complete:

```bash
python3 -m experiments.e08_compiled_control
MPLCONFIGDIR=/tmp/deltaalign-matplotlib python3 -m experiments.summarize_compiled_control
python3 -m unittest discover -s tests -v
```

[E08 findings](docs/e08_findings.md) isolate graph maintenance from solver reuse. At requested 0.1%, selective maintenance + SciPy beats full recomputation by 1.45–1.86×, while warm repair wins in three of four paired conditions. At 1%, compiled selective is 2.33–6.52× faster than warm repair; full recomputation wins at 5%. Exact oracle equality and 37 tests pass. Next use persistent-state streams and count initialization; these reset timings do not establish stream performance. [Paper readiness](docs/PAPER_READINESS.md) is updated.


The persistent-state stream pilot is complete:

```bash
python3 -m experiments.e09_streams
MPLCONFIGDIR=/tmp/deltaalign-matplotlib python3 -m experiments.summarize_streams
python3 -m unittest discover -s tests -v
```

[E09 findings](docs/e09_findings.md) report 40 ten-step streams, 400 exact updates and 38 passing tests. At requested 0.1%, feature maintenance improves 9.05–9.46× and the compiled selective pipeline improves 1.42–1.85× after initialization. Warm initialization prevents a total win over ten updates, despite stage gains. At 1%, features still improve about 1.7× but cost refresh regresses; compiled selective still improves setup-inclusive totals by 1.11–1.19×. Component gains count as positive outcomes and are reported separately from overall latency. Independent streams expose severe hidden-correspondence decline even in full recomputation; no truth-quality benefit is claimed. Next optimize the isolated cost stage using [the design](docs/cost_maintenance_design.md), then test topology robustness. [Paper readiness](docs/PAPER_READINESS.md) records progress and limits.


Persistent normalized cost maintenance is implemented and evaluated:

```bash
python3 -m experiments.e10_costs
MPLCONFIGDIR=/tmp/deltaalign-matplotlib python3 -m experiments.summarize_costs
python3 -m unittest discover -s tests -v
```

[E10 findings](docs/e10_findings.md): 400 exact updates, identical full SciPy mappings and 41 passing tests. Cost refresh improves 1.23–1.27× at 0.1% batches and 1.75–1.77× at 1% versus historical refresh. Setup-inclusive totals improve about 1–7% over the previous selective pipeline; this component gain counts as positive progress independently of its modest overall effect. The cache uses disjoint cost blocks, dirty-only normalization and in-place dense updates, with 432 KB of extra normalized feature arrays at 1K. At 1%, full cost construction still wins slightly. Matching quality is unchanged. Next test [topology robustness](docs/topology_robustness_design.md) on fresh seeds 55–59; [paper readiness](docs/PAPER_READINESS.md) is updated.


The topology robustness gate is complete:

```bash
python3 -m experiments.e11_topology
MPLCONFIGDIR=/tmp/deltaalign-matplotlib python3 -m experiments.summarize_topology
python3 -m unittest discover -s tests -v
```

[E11 findings](docs/e11_findings.md): 120 BA/ER/WS streams, 1,200 exact updates, 360 no-update controls and 42 tests passing. At requested 0.1%, feature-stage speedups are about 9×/13×/16× and setup-inclusive speedups are 1.40–1.63×/1.93–2.91×/1.25–1.60× across the respective topologies. At 1%, total medians improve 1.14–1.45×. Stage gains count independently of total gains. Initial WS NC is only 33.58% at 1% noise and 6.94% at 5%, so strong correspondence-quality claims remain unsupported. Next [profile isolated peak RSS and size viability](docs/resource_scaling_design.md) before a broad larger-size run. [Paper readiness](docs/PAPER_READINESS.md) records both progress and limits.


The isolated resource profile is complete:

```bash
python3 -m experiments.e12_resources
MPLCONFIGDIR=/tmp/deltaalign-matplotlib python3 -m experiments.summarize_resources
python3 -m unittest discover -s tests -v
```

[E12 findings](docs/e12_findings.md): 18 sequential fresh-worker profiles at 1K/2K/5K, identical cross-worker fingerprints at all 36 paired snapshots and 43 tests passing. At 5K, features improve 6.52–18.53× and costs 1.98–5.45×; total ratios are only 1.03–1.18× in this single seed. Maintained peak RSS is 318–349 MiB, about 5–15% higher than full recomputation. Component savings count as progress independently of small total gains and memory regression. This is a viability profile, not replicated scaling evidence. Next [replicate bounded 2K/5K comparisons](docs/replicated_scaling_design.md) on fresh seeds 61–65. [Paper readiness](docs/PAPER_READINESS.md) retains quality and novelty limits.


Bounded replicated scaling is complete:

```bash
python3 -m experiments.e13_scaling
MPLCONFIGDIR=/tmp/deltaalign-matplotlib python3 -m experiments.summarize_scaling
python3 -m unittest discover -s tests
```

E13 bounded replication completed: 60 sequential fresh workers, 30 paired seed bundles (61–65) at 2K/5K across BA/ER/WS, with all 120 setup/update fingerprints and objectives exact; 44 tests pass. At 5K, median feature gains are 7.74–17.92× and cost gains 1.84–5.42×. Setup-inclusive medians are 1.03× BA, 1.24× ER and 1.03× WS; all 30 observed pairs favor maintenance, but small BA/WS effects require repeated timing. Median persistent/full peak-RSS ratios at 5K are 1.17/1.14/1.06. Component gains count as positive paper progress; assignment dominance, quadratic storage, weak WS quality and unverified novelty remain. See [E13 findings](docs/e13_findings.md) and [paper readiness](docs/PAPER_READINESS.md).

Next: [primary-source contribution audit](docs/post_e13_research_gate.md).


The [E14 component audit](docs/literature_component_audit.md) and [contribution decision](docs/e14_findings.md) are complete. Existing work overlaps with structural histograms, incremental representation maintenance and assignment repair, so algorithm novelty remains unestablished. E13's replicated component gains still count as progress. Next implement [E15 attribution](docs/e15_protocol.md), comparing refined maintenance against conservative locality controls with the same objective and solver. [Configuration](configs/e15_attribution.json) is preregistered; E15 has not run. [Paper readiness](docs/PAPER_READINESS.md) retains memory, timing and correspondence-quality gaps.


E15 attribution is complete:

```bash
python3 -m experiments.e15_attribution
MPLCONFIGDIR=/tmp/deltaalign-matplotlib python3 -m experiments.summarize_attribution
python3 -m unittest discover -s tests
```

E15 attribution completed: 120 fresh workers, 30 paired ten-step streams, 1,200 method updates and all 990 full-versus-maintained snapshots exact; 46 tests pass. At sparse 0.1% updates, refined features improve 1.12–1.41× and costs 1.43–1.65× over conservative locality controls. Refined feature time wins on all 30 seeds; BA 1% bare cost time has a 0.99× median ratio despite fewer entries. Total differences versus conservative controls are small; gains over full largely come from locality shared by all maintained methods. Component improvements count positively. Novelty, WS quality, dense memory and repeated small-effect timing remain limits.

See [E15 findings](docs/e15_findings.md), [attribution plot](results/figures/e15_attribution.png) and [second-layer work/time plot](results/figures/e15_second_layer.png). Next: [E16 fixed-job timing repetition](docs/e16_protocol.md).


E16 repeated fixed-job timing is complete:

```bash
python3 -m experiments.e16_timing
MPLCONFIGDIR=/tmp/deltaalign-matplotlib python3 -m experiments.summarize_timing
python3 -m unittest discover -s tests
```

E16 completed: 60 sequential fresh workers, three execution rounds per fixed 5K BA/WS job, all 120 paired snapshots matching each other and E13, and 47 tests passing. Across five per-seed medians, setup-inclusive ratios are 1.039× BA and 1.034× WS. BA favors maintenance in 15/15 executions; WS in 14/15, with one seed-63 reversal and overlapping timing ranges. Repeated feature/cost medians are 7.79×/1.86× BA and 17.96×/5.37× WS. Median maintained/full peak-RSS ratios are 1.182/1.058. Component progress remains positive; modest total benefits, WS variability, memory regression, weak correspondence and novelty overlap remain explicit.

See [E16 findings](docs/e16_findings.md) and [timing plot](results/figures/e16_timing.png). Next: [real-topology provenance and initial-quality gate](docs/real_topology_gate.md).

# Next resource gate: isolated size and memory profiling

After E11 topology evidence, test resource viability before a broad larger-size benchmark. This is a one-seed profile gate, not a statistically replicated speedup claim. Use fresh seed 60, BA/ER/WS frozen parameters, sizes 1K, 2K and 5K, 1% initial noise and three successive shared-latent 0.1% batches. Compare persistent normalized-cost + selective-feature + SciPy with full recomputation + SciPy. Do not add warm assignment, tuning, parallel workers or longer streams in this gate.

Run each method/size/family in a fresh sequential subprocess. The parent retains small result records only, not graph/cost arrays. Measure whole-worker peak RSS with the operating system, report imports/generation/initialization/updates/validation included in that peak, and measure graph-to-assignment stages/setup separately. Also record dense matrix and extra cache array bytes. One float64 5K cost matrix occupies 200 MB before temporaries, graphs and solver workspace.

Before 5K, inspect available memory and applicable process/container limits; estimate headroom for dense matrices, block temporaries and graphs. Start at 1K/2K and record any resource ceiling rather than launching an unsafe larger sweep. Do not label array bytes as RSS. Record machine/CPU/software and resource limits with the results.

Use frozen E10/E11 numerical kernels. Discard baseline full costs after evaluating/hashing each step if they are no longer required, so full recomputation does not retain an unnecessary previous dense matrix solely for the benchmark. Cached costs must persist for selective maintenance. Document this lifecycle difference explicitly; preserve numerical operations and count required memory. Avoid keeping a full oracle and optimized cache together in the measured worker.

Verify full/selective equality across isolated workers via reproducible fingerprints of feature arrays, normalized features, cost matrices, scale and mappings at every step. Hash contiguous buffers directly, outside timed stages, without allocating another dense matrix via `tobytes`. Store objectives and NC/S3 as well. Fingerprints are a cross-worker reproducibility check, not a replacement for existing bitwise small-instance tests. Peak RSS includes this validation work, whose allocation strategy must be stated.

Report feature/cost/solver stage and initialization-inclusive latency by size/topology, with a single-run limitation. Component improvements count positively even if total scaling is limited by dense assignment. If 5K is viable, design the replicated scaling benchmark afterward; if not, identify the resource bottleneck before changing the algorithm. Exactness does not address E11's weak WS/high-noise initial alignment quality or independent-stream correspondence decline. Literature novelty, long streams and certified CPU decomposition remain separate gates.


## Completed E12

See [E12 findings](e12_findings.md): 5K is viable under measured headroom, with exact cross-worker snapshots. Component gains persist, total improvements are small in BA/WS, and maintained peak RSS is higher. Next [replicate bounded 2K/5K comparisons](replicated_scaling_design.md) rather than extrapolate a one-seed timing result.

# E00 locality protocol

This experiment diagnoses locality of a particular baseline, rather than claiming a general alignment result. Generate undirected BA graphs with attachment count 3 and fixed integer vertex sets. A hidden random permutation creates the target. Mixed edge edits totaling 1% of target edges provide initial observation noise. A noiseless case is a correctness control. Never expose the hidden permutation to matching.

Descriptors are log1p(degree, neighbor-degree mean, neighbor-degree standard deviation). Initial pooled descriptor standard deviations define normalization, frozen across updates; dimensions with negligible spread use scale 1e-12. Costs are squared Euclidean distances. FullAlign solves dense exact linear assignment in stable vertex order using the installed SciPy solver. Repeat no-update solves to check determinism; ties can still yield equivalent mappings and therefore must limit interpretation.

Only the source receives uniform mixed updates initially. Insertion count rounds half upward; deletions take the remaining budget. Sample deletions from existing edges and insertions from pre-update nonedges, without loops or duplicates. Each trial starts from its original graph pair. Define requested fractions using combined pre-update edge counts, round half upward with minimum one edit, and log realized budgets. Separate seeds derived from a seed bundle govern graph, permutation, noise, and updates. All radii reuse a single new full solve.

Measure region radii 0–3 on the union of pre/post source graphs, seeded by changed edge endpoints. Log NC, EC, S3, objective, mapping changes, RF, precision, recall, and no-update determinism. Undefined denominators produce null, including recall when no mappings change. Compare initial NC/structure with a random permutation. Timings include descriptors, dense costs, and assignment; experiment bookkeeping and diagnostic metrics are outside full solver runtime. These timings are not incremental update latency.

Run correctness cases, then 100-node smoke, then five seeds at 1K. Profile 5K only if the baseline-quality gate permits meaningful locality interpretation. Poor NC or ties require a baseline revision before repair code. The configured 1K/5K matrix is available but does not override this gate.

## Descriptor revision

Preserve the basic descriptor and compare `degree_hist` and `two_hop_hist` on the same 1K seed bundles and batches. Fixed degree-bin boundaries are `[0,1,2,3,4,5,7,10,15,25,50,100,infinity]`. `degree_hist` appends log1p neighbor-degree bin counts to the basic features. `two_hop_hist` additionally appends log1p averages of those counts over neighbors. These choices are shared by both graphs, independent of IDs and truth, and recorded before the comparison runs. Feature dependency radii are respectively 1 and 2 around edited endpoints. Initial pooled scaling and the solver remain unchanged. Descriptor selection on these development seeds requires subsequent independent validation.

Noiseless controls measure exact descriptor duplication, zero-cost assignment behavior, and NC for each mode. Replay one/six-edit trials for the two-hop descriptor to record radius-2 misses and mapping changes whose source features remain unchanged. Preserve all original outputs. Report undefined recall separately; it is not counted as perfect recall.

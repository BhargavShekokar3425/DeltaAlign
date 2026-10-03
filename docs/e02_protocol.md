# E02 margin pruning and confidence-seed protocol

## Motivation from E01

Unconditional K=5 ownership closure recovered about 97% of dense mapping changes at 0.1% source updates but included about 95% of nodes in both seed splits. Exact feature seeds reduced some structural overexpansion but did not prevent candidate chains. Therefore test **candidate admission** and **seed admission** separately, with unpruned K=5 and radius-2 controls. Remain at 1K; do not claim update speedup or proceed to parallel repair.

## Fixed choices before running

Retain BA attachment 3, fixed vertices, two_hop_hist, 1% target noise, frozen initial normalization, exact full assignment, requested combined-edge fractions 0.01%, 0.1%, 1%, 5%, and source/target/both update protocols. Development seeds are 0–4. Seeds 5–9 were already inspected in E01, so fresh validation seeds are 10–14. Odd both-graph budgets assign the extra edit to source; one-edit both trials duplicate source trials and must not be pooled as independent evidence.

For candidate cap K in {5,20}, retain ranked targets whose distance is at most row-best distance plus a margin in {0,0.01,0.05,0.1,0.5}, using squared normalized distance divided by feature dimension. Always add the old mapping even when outside the cap or threshold. Candidate sizes are at most K+1. This is row-best-relative pruning, not pruning relative to a known global optimum. It can exclude globally necessary assignments; log changed-mapping candidate coverage and every excluded full-match vertex. Deterministic target ordering handles ties.

Compare support seeds and exact changed-feature dependency seeds. For the latter, also test confidence filtering: pressure is max(old-assignment regret against the new row minimum, positive old-assignment cost degradation), both in mean-per-feature units. Select only dependency-pool rows with pressure strictly above thresholds {0,0.01,0.05,0.1}. This explicitly risks false negatives and is an empirical ablation. Target dependencies include old/new reverse indexes and changed candidate lists. No true mapping or new full optimum is used by these detectors.

Cache exact dense costs. Rescore changed source rows and changed target columns; if a target changes, refresh all source rankings to include new entrants. Compare refreshed costs, rankings, and pruned candidate sets against full refresh in each trial. Full feature recomputation remains an oracle, not an incremental implementation. Verify old-match feasibility and candidate ownership closure. Report recall/precision/RF, seed size, closure growth, full-match candidate coverage, and missed vertices. Undefined recall on zero-change trials is excluded with counts recorded. Report development and fresh validation separately.

## Selection and validation gate

Complete all development settings and controls before reading fresh validation outcomes. Group sparse development trials by update side and requested fraction. A promising setting must have group mean RF <=20%, group mean recall >=95% for each nonempty group, and minimum nonempty trial recall >=90%. These are internal decision guides, not scientific thresholds. Require all changed full-match targets to remain among candidates in development for a setting to qualify for exact-recovery investigation.

If any setting qualifies, choose the lowest worst-group mean RF, then highest worst-group recall with deterministic parameter tie-breaking. Otherwise label the selection **exploratory, gate failed**: among settings under the RF budget choose highest worst-group recall, then minimum trial recall and lowest RF. If none fit the RF budget, choose the lowest worst-group RF. Freeze exactly one setting in a selection JSON before running validation. Evaluate only that selected setting plus controls on fresh seeds; do not sweep validation margins.

Treat validation as a diagnostic test of the frozen setting, not a chance to tune it. Log config/source hashes and preserve E00/E01 outputs. Report 1%/5% stress trials, but select settings using sparse updates only. If pruning improves compactness but loses dense recovery, measure the quality of an actual constrained repair in a later small pilot rather than equating missed mappings with objective degradation. If even that cannot justify locality, reconsider the formulation.

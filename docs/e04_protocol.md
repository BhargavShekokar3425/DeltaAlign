# E04 constant-bin correction and paired objective review

E03 found normalization-dominated costs in 6/30 1%-update trials and 24/30 5%-update trials. Neither sparse update fraction was affected. It also found a compact dense region with substantially better objective fidelity than the pruned candidate solve, and keep-old with higher NC/S3 than full descriptor recomputation. E04 must distinguish an actual normalization correction from improvements due to changed seeds or policy tuning.

## Fixed correction

Compute pooled initial descriptor standard deviations. Dimensions with std <=1e-12 use scale 1.0 in the original log-feature units; other dimensions retain their measured standard deviation. Freeze this scale for the entire trial family. A previously constant bin therefore gains a finite structural weight when it becomes active. Do not drop the bin, recompute the scale after updates, change margins, or search floor values. This corrects the near-infinite weighting defect; it does not guarantee the resulting objective corresponds to ground truth or edge conservation.

Preserve the original FullAlign default and all earlier outputs as historical references. The corrected experiment explicitly passes the new scale to the existing solver. Keep the E02 cap/margin/confidence policy frozen and verify its original detector/config/evidence hashes.

## Paired comparison and fresh seeds

Run both historical epsilon-floor scaling and corrected unit-constant scaling on identical graph pairs and reset edge batches. Use seeds 15–19 as observed replay and 20–24 as fresh fixed-policy confirmation. Compare modes only as paired observations and evaluate mappings under their own stated shared objective; costs under different objectives are not directly interchangeable. No selection occurs on either seed group. The nonconstant scale is identical between modes; initially constant features contribute zero to all pairwise initial distances, so initial costs and old mappings must agree.

Retain 1K BA graphs, attachment 3, 1% target noise, two_hop_hist, source/target/both updates, and fractions 0.01%, 0.1%, 1%, 5%. Compare all seven E03 methods. One-edit both cases duplicate source-only cases; report side groups separately. Regression checks cover newly active bin cost, pooled scale, frozen scale, noiseless objective, and invalid inputs. In every trial check cached costs/candidates against full refresh, bijection/frozen/candidate constraints, and full/repair/old objective ordering.

Record active constant dimensions, objective magnitudes, RF/FRA, NC/S3, full/keep-old differences, candidate-versus-region loss decomposition, and available objective gain recovered. Show the previous sparse quality guides unchanged as descriptive review, not as a new scientific success criterion. Preserve stress results now that the correction makes their objective weights finite. Timings still use full feature/dense-cost oracles and must not be presented as end-to-end speedup.

## Decisions and paper progress

If normalization dominates historical stress results, identify the affected cases explicitly. Check whether keep-old remains stronger on NC/S3 after correction. If it does, decide the stated maintenance objective before adding further localization complexity. Any new objective or localization policy needs a fixed protocol, fair full and dynamic-assignment controls, and fresh validation; do not tune the E02 policy to make this correction appear successful.

Report whether this step improves scientific reliability and whether it supplies evidence for the intended efficient-repair paper. A numerical fix alone is infrastructure progress, not a method contribution or publishability guarantee.

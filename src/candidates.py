"""Exact diagnostic candidate maintenance using a cached dense cost matrix.

Changed target columns are rescored for every source, including new top-K
entrants. This is a correctness reference, not a sublinear production index.
"""
import numpy as np
from scipy.spatial.distance import cdist


def candidate_lists(costs, mapping, k):
    n = costs.shape[0]
    if costs.shape != (n, n) or len(mapping) != n or len(set(mapping)) != n:
        raise ValueError('Expected square costs and a bijective old mapping')
    if not 1 <= k <= n:
        raise ValueError('k must lie between 1 and n')
    # Stable sort makes equal-cost choices deterministic in target ID order.
    ranked = np.argsort(costs, axis=1, kind='stable')[:, :k]
    return [frozenset([int(mapping[u]), *ranked[u].tolist()]) for u in range(n)]


def reverse_index(candidates):
    reverse = {}
    for u, targets in enumerate(candidates):
        for target in targets:
            reverse.setdefault(target, set()).add(u)
    return reverse


def refresh_costs(old_costs, source, target, changed_source, changed_target, scale):
    costs = old_costs.copy()
    rows, columns = sorted(changed_source), sorted(changed_target)
    if rows:
        costs[rows, :] = cdist(source[rows] / scale, target / scale, 'sqeuclidean')
    if columns:
        costs[:, columns] = cdist(source / scale, target[columns] / scale, 'sqeuclidean')
    return costs, len(rows) * len(target) + len(columns) * (len(source) - len(rows))


def update_candidates(old_candidates, costs, changed_source, changed_target, mapping, k):
    # All sources are eligible when a target changed: the old reverse index
    # alone cannot discover a previously absent target entering the top-K.
    dirty = set(range(len(mapping))) if changed_target else set(changed_source)
    candidates = list(old_candidates)
    for u in sorted(dirty):
        top = np.argsort(costs[u], kind='stable')[:k]
        candidates[u] = frozenset([int(mapping[u]), *top.tolist()])
    return candidates, dirty


def dependency_seeds(source_seeds, target_seeds, mapping, old_candidates, new_candidates):
    inverse = np.empty(len(mapping), dtype=int)
    inverse[mapping] = np.arange(len(mapping))
    seeds = set(source_seeds) | {int(inverse[v]) for v in target_seeds}
    old_reverse, new_reverse = reverse_index(old_candidates), reverse_index(new_candidates)
    for v in target_seeds:
        seeds.update(old_reverse.get(v, set()))
        seeds.update(new_reverse.get(v, set()))
    seeds.update(u for u, (old, new) in enumerate(zip(old_candidates, new_candidates)) if old != new)
    return seeds

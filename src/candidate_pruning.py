"""Empirical cost-margin pruning and update-pressure seed selection.

These policies preserve old matches, but do not guarantee recovery of the
optimal dense assignment. Costs are compared in mean-per-feature units.
"""
import numpy as np


def ranked_targets(costs, k):
    if costs.ndim != 2 or costs.shape[0] != costs.shape[1] or not np.isfinite(costs).all():
        raise ValueError('Expected finite square costs')
    if not 1 <= k <= len(costs):
        raise ValueError('Invalid candidate cap')
    return np.argsort(costs, axis=1, kind='stable')[:, :k]


def refresh_rankings(old_rankings, costs, changed_source, changed_target):
    dirty = set(range(len(costs))) if changed_target else set(changed_source)
    rankings = old_rankings.copy()
    if dirty:
        rows = sorted(dirty)
        rankings[rows] = np.argsort(costs[rows], axis=1, kind='stable')[:, :old_rankings.shape[1]]
    return rankings, dirty


def pruned_candidates(costs, mapping, k, margin, dimensions, rankings=None):
    if margin < 0 or dimensions <= 0:
        raise ValueError('Margin must be nonnegative and dimensions positive')
    n = len(costs)
    if len(mapping) != n or set(mapping) != set(range(n)):
        raise ValueError('Old mapping must be a permutation')
    if not 1 <= k <= n:
        raise ValueError('Invalid candidate cap')
    if rankings is None:
        rankings = ranked_targets(costs, k)
    if rankings.shape[0] != n or rankings.shape[1] < k:
        raise ValueError('Insufficient ranked targets')
    lists = []
    for u in range(n):
        top = rankings[u, :k]
        cutoff = costs[u, top[0]] + margin * dimensions
        admitted = top[costs[u, top] <= cutoff]
        lists.append(frozenset([int(mapping[u]), *admitted.tolist()]))
    return lists


def refresh_pruned_candidates(old_candidates, costs, mapping, k, margin, dimensions, rankings, dirty):
    candidates = list(old_candidates)
    for u in sorted(dirty):
        top = rankings[u, :k]
        cutoff = costs[u, top[0]] + margin * dimensions
        candidates[u] = frozenset([int(mapping[u]), *top[costs[u, top] <= cutoff].tolist()])
    return candidates


def confidence_seeds(pool, old_costs, new_costs, mapping, dimensions, threshold):
    if threshold < 0 or dimensions <= 0:
        raise ValueError('Invalid confidence threshold or dimension count')
    rows = np.arange(len(mapping))
    assigned_new = new_costs[rows, mapping]
    regret = np.maximum(0, assigned_new - new_costs.min(axis=1)) / dimensions
    degradation = np.maximum(0, assigned_new - old_costs[rows, mapping]) / dimensions
    pressure = np.maximum(regret, degradation)
    # Strict comparison prevents zero-pressure changes from seeding closure.
    return {u for u in pool if pressure[u] > threshold}, pressure

"""Exact restricted assignment for objective-fidelity diagnostics."""
from time import perf_counter
import numpy as np
from scipy.optimize import linear_sum_assignment


def restricted_assignment(costs, old_mapping, affected, candidates=None):
    n = len(old_mapping)
    if costs.shape != (n, n) or not np.isfinite(costs).all():
        raise ValueError('Expected finite square costs')
    if set(old_mapping) != set(range(n)):
        raise ValueError('Old mapping must be a permutation')
    affected = set(affected)
    if not affected <= set(range(n)):
        raise ValueError('Repair vertices outside source set')
    sources = sorted(affected)
    targets = sorted(int(old_mapping[u]) for u in sources)
    start = perf_counter()
    result = old_mapping.copy()
    if sources:
        local = costs[np.ix_(sources, targets)].copy()
        if candidates is not None:
            target_set = set(targets)
            for row, u in enumerate(sources):
                if int(old_mapping[u]) not in candidates[u]:
                    raise ValueError('Old-match feasibility edge missing')
                if not set(candidates[u]) <= target_set:
                    raise ValueError('Candidate targets escape ownership closure')
                local[row, [i for i, v in enumerate(targets) if v not in candidates[u]]] = np.inf
        rows, columns = linear_sum_assignment(local)
        if not np.isfinite(local[rows, columns]).all():
            raise RuntimeError('Restricted assignment infeasible')
        result[np.array(sources)[rows]] = np.array(targets)[columns]
    if set(result) != set(range(n)):
        raise RuntimeError('Merge is not bijective')
    frozen = sorted(set(range(n)) - affected)
    if not np.array_equal(result[frozen], old_mapping[frozen]):
        raise RuntimeError('Frozen mapping changed')
    if candidates is not None and any(int(result[u]) not in candidates[u] for u in sources):
        raise RuntimeError('Candidate constraint violated')
    return result, {'restricted_solve_time': perf_counter()-start,
                    'repair_size': len(sources), 'target_size': len(targets)}

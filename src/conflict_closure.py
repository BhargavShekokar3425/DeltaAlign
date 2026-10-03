from collections import deque
import numpy as np


def conflict_closure(seeds, candidates, mapping):
    n = len(mapping)
    if len(set(mapping)) != n or set(mapping) != set(range(n)):
        raise ValueError('Old mapping must be a permutation')
    inverse = np.empty(n, dtype=int)
    inverse[mapping] = np.arange(n)
    affected = set(seeds)
    queue = deque(sorted(seeds))
    scanned, depths = 0, {u: 0 for u in seeds}
    while queue:
        u = queue.popleft()
        for target in sorted(candidates[u]):
            scanned += 1
            owner = int(inverse[target])
            if owner not in affected:
                affected.add(owner)
                depths[owner] = depths[u] + 1
                queue.append(owner)
    return affected, {'candidate_edges_scanned': scanned,
                      'closure_depth': max(depths.values(), default=0),
                      'closure_added': len(affected) - len(seeds)}

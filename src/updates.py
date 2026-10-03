import numpy as np


def apply_batch(graph, count, seed, insertion_fraction=0.5):
    if count < 0 or not 0 <= insertion_fraction <= 1:
        raise ValueError("Invalid update budget or insertion fraction")
    result = graph.copy()
    rng = np.random.default_rng(seed)
    edges = sorted(tuple(sorted(e)) for e in graph.edges())
    insertions = int(count * insertion_fraction + 0.5)
    deletions = count - insertions
    n = graph.number_of_nodes()
    if deletions > len(edges) or insertions > n * (n - 1) // 2 - len(edges):
        raise ValueError("Budget exceeds available edges/nonedges")
    removed = [edges[i] for i in rng.choice(len(edges), deletions, replace=False)] if deletions else []
    added = set()
    while len(added) < insertions:
        u, v = sorted(rng.choice(n, 2, replace=False).tolist())
        if not graph.has_edge(u, v):
            added.add((u, v))
    result.remove_edges_from(removed)
    result.add_edges_from(sorted(added))
    return result, {"inserted": sorted(added), "deleted": removed}

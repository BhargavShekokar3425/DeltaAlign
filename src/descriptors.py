import numpy as np


def descriptors(graph, mode="basic"):
    if mode not in {"basic", "degree_hist", "two_hop_hist"}:
        raise ValueError(f"Unknown descriptor mode: {mode}")
    degree = np.array([graph.degree(u) for u in range(len(graph))], dtype=float)
    features = np.zeros((len(graph), 3))
    for u in range(len(graph)):
        neighbors = list(graph.neighbors(u))
        # Stable value order avoids roundoff changes when graph copies reorder
        # adjacency iteration, even though the neighborhood is unchanged.
        values = np.sort(degree[neighbors])
        features[u] = [degree[u], values.mean() if len(values) else 0,
                       values.std() if len(values) else 0]
    basic = np.log1p(features)
    if mode == "basic":
        return basic
    # Fixed degree bins are shared by both graphs and never depend on node IDs.
    bins = np.array([0, 1, 2, 3, 4, 5, 7, 10, 15, 25, 50, 100, np.inf])
    histogram = np.zeros((len(graph), len(bins) - 1))
    for u in range(len(graph)):
        histogram[u] = np.histogram(degree[list(graph.neighbors(u))], bins=bins)[0]
    if mode == "degree_hist":
        return np.column_stack([basic, np.log1p(histogram)])
    # Neighbor averages capture a second structural layer without expanding
    # whole BFS balls, which rapidly cover BA graphs.
    second = np.zeros_like(histogram)
    for u in range(len(graph)):
        neighbors = list(graph.neighbors(u))
        if neighbors:
            second[u] = histogram[neighbors].mean(axis=0)
    return np.column_stack([basic, np.log1p(histogram), np.log1p(second)])

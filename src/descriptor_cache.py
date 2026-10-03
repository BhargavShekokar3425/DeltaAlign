"""Exact fixed-vertex two-hop descriptors with batch dependency maintenance.

Caller supplies old/new graphs and the complete applied edge batch. Caches are
mutated; clone them for reset trials. No hidden correspondence is consumed.
"""
from dataclasses import dataclass
from time import perf_counter
import numpy as np

BINS = np.array([0, 1, 2, 3, 4, 5, 7, 10, 15, 25, 50, 100, np.inf])


@dataclass
class DescriptorCache:
    degree: np.ndarray
    histogram: np.ndarray
    features: np.ndarray

    def copy(self):
        return DescriptorCache(self.degree.copy(), self.histogram.copy(), self.features.copy())

    @property
    def nbytes(self):
        return self.degree.nbytes + self.histogram.nbytes + self.features.nbytes


def _basic(graph, degree, u):
    values = np.sort(degree[list(graph.neighbors(u))])
    return np.log1p([degree[u], values.mean() if len(values) else 0,
                     values.std() if len(values) else 0])


def _second(graph, histogram, u):
    neighbors = list(graph.neighbors(u))
    return np.log1p(histogram[neighbors].mean(axis=0)) if neighbors else np.zeros(len(BINS)-1)


def initialize(graph):
    n = len(graph)
    if set(graph) != set(range(n)) or graph.is_directed() or graph.is_multigraph():
        raise ValueError('Expected a simple undirected fixed-vertex graph')
    degree = np.array([graph.degree(u) for u in range(n)], dtype=float)
    histogram = np.array([np.histogram(degree[list(graph.neighbors(u))], bins=BINS)[0]
                          for u in range(n)], dtype=float).reshape(n, len(BINS)-1)
    features = np.zeros((n, 3+2*(len(BINS)-1)))
    for u in range(n):
        features[u] = np.concatenate([_basic(graph, degree, u), np.log1p(histogram[u]),
                                      _second(graph, histogram, u)])
    return DescriptorCache(degree, histogram, features)


def update(cache, old_graph, new_graph, batch):
    start = perf_counter()
    if len(old_graph) != len(cache.degree) or set(old_graph) != set(new_graph):
        raise ValueError('Vertex sets must stay fixed')
    endpoints = {u for kind in ['inserted', 'deleted'] for edge in batch[kind] for u in edge}
    support = set(endpoints)
    for u in endpoints:
        support.update(old_graph.neighbors(u))
        support.update(new_graph.neighbors(u))
    support_time = perf_counter()-start
    start = perf_counter()
    for u in endpoints:
        cache.degree[u] = new_graph.degree(u)
    # Retain old feature rows only within the eventual support. Histogram
    # changes, rather than every conservative row, propagate one layer farther.
    changed_histograms = set()
    basic_values = {}
    for u in sorted(support):
        basic_values[u] = _basic(new_graph, cache.degree, u)
        h = np.histogram(cache.degree[list(new_graph.neighbors(u))], bins=BINS)[0]
        if not np.array_equal(h, cache.histogram[u]):
            changed_histograms.add(u)
            cache.histogram[u] = h
    first_layer_time = perf_counter()-start
    start = perf_counter()
    second_support = set(endpoints)
    for u in changed_histograms:
        second_support.update(old_graph.neighbors(u))
        second_support.update(new_graph.neighbors(u))
    second_support_time = perf_counter()-start
    start = perf_counter()
    total_support = sorted(support | second_support)
    old_rows = cache.features[total_support].copy()
    for u in sorted(support):
        cache.features[u, :3] = basic_values[u]
        cache.features[u, 3:15] = np.log1p(cache.histogram[u])
    for u in sorted(second_support):
        cache.features[u, 15:] = _second(new_graph, cache.histogram, u)
    second_layer_time = perf_counter()-start
    start = perf_counter()
    changed = {total_support[i] for i in np.flatnonzero(np.any(cache.features[total_support] != old_rows, axis=1))}
    equality_time = perf_counter()-start
    return changed, {'endpoints': len(endpoints), 'first_layer_support': len(support),
                     'changed_histograms': len(changed_histograms), 'second_layer_support': len(second_support),
                     'total_support': len(total_support), 'changed_features': len(changed),
                     'support_time': support_time+second_support_time,
                     'first_layer_time': first_layer_time, 'second_layer_time': second_layer_time,
                     'equality_time': equality_time}

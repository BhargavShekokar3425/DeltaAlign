from time import perf_counter
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from .descriptors import descriptors


def full_align(g, h, scale=None, descriptor_mode="basic"):
    start = perf_counter()
    fg, fh = descriptors(g, descriptor_mode), descriptors(h, descriptor_mode)
    feature_time = perf_counter() - start
    if scale is None:
        scale = np.maximum(np.vstack([fg, fh]).std(axis=0), 1e-12)
    costs = cdist(fg / scale, fh / scale, metric="sqeuclidean")
    cost_time = perf_counter() - start - feature_time
    solve_start = perf_counter()
    rows, columns = linear_sum_assignment(costs)
    mapping = np.empty(len(g), dtype=int)
    mapping[rows] = columns
    return mapping, scale, {"objective": float(costs[rows, columns].sum()),
        "runtime": perf_counter() - start, "feature_time": feature_time,
        "cost_time": cost_time, "assignment_time": perf_counter() - solve_start}

"""Current FullAlign entry point with finite constant-bin normalization.

src.full_align remains the historical solver entry point used by frozen runs.
"""
from time import perf_counter
import numpy as np
from .descriptors import descriptors
from .normalization import initial_scale
from .full_align import full_align as historical_align


def full_align(g, h, scale=None, descriptor_mode='basic'):
    start = perf_counter()
    if scale is None:
        scale = initial_scale(descriptors(g, descriptor_mode), descriptors(h, descriptor_mode))
    scale = np.asarray(scale, dtype=float)
    if scale.ndim != 1 or not np.isfinite(scale).all() or np.any(scale <= 0):
        raise ValueError('Scale must be a finite positive vector')
    normalization_time = perf_counter()-start
    mapping, scale, stats = historical_align(g, h, scale=scale, descriptor_mode=descriptor_mode)
    stats['runtime'] = perf_counter()-start
    stats['normalization_time'] = normalization_time
    stats['normalization'] = 'unit_constant'
    return mapping, scale, stats

"""Finite, frozen descriptor scaling for newly active structural bins."""
import numpy as np


def initial_scale(source_features, target_features, constant_tolerance=1e-12):
    source_features, target_features = np.asarray(source_features), np.asarray(target_features)
    if source_features.ndim != 2 or source_features.shape != target_features.shape or not len(source_features):
        raise ValueError('Expected equal nonempty descriptor matrices')
    if not np.isfinite(source_features).all() or not np.isfinite(target_features).all():
        raise ValueError('Descriptor values must be finite')
    if not np.isfinite(constant_tolerance) or constant_tolerance < 0:
        raise ValueError('Invalid constant-dimension tolerance')
    spread = np.vstack([source_features, target_features]).std(axis=0)
    # Unit scale in the original log-feature units gives formerly constant
    # bins a finite weight if they later activate. Freeze all scales thereafter.
    return np.where(spread <= constant_tolerance, 1.0, spread)

"""Compare mappings on the same updated dense objective."""
import numpy as np


def objective(costs, mapping):
    return float(costs[np.arange(len(mapping)), mapping].sum())


def fidelity(costs, mapping, full_mapping, old_mapping):
    j, full, old = (objective(costs, m) for m in [mapping, full_mapping, old_mapping])
    tolerance = 1e-10 * max(1., abs(j), abs(full), abs(old))
    if j < full - tolerance:
        raise RuntimeError('Restricted result improves on asserted full optimum')
    if j > old + tolerance:
        raise RuntimeError('Repair worsens feasible old mapping')
    absolute = max(0., j-full)
    available = old-full
    return {'objective': j, 'full_objective': full, 'old_objective': old,
            'absolute_objective_gap': absolute,
            'relative_objective_gap': absolute/abs(full) if full != 0 else None,
            'objective_gain_recovered': (old-j)/available if available > tolerance else None,
            'full_recompute_agreement': float(np.mean(mapping == full_mapping)),
            'mapping_churn': float(np.mean(mapping != old_mapping))}

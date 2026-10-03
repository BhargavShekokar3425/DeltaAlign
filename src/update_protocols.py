"""Controlled shared-latent versus independent balanced graph updates.

The hidden permutation is used only by the dataset generator.
"""
import numpy as np
from .updates import apply_batch


def paired_updates(g, h, permutation, per_graph_budget, source_seed, target_seed, protocol):
    n = len(g)
    if set(permutation) != set(range(n)) or set(g) != set(range(n)) or set(h) != set(range(n)):
        raise ValueError('Expected fixed equal vertex sets and a hidden permutation')
    if protocol not in {'shared_latent', 'independent'}:
        raise ValueError('Unknown update protocol')
    new_g, gb = apply_batch(g, per_graph_budget, source_seed)
    if protocol == 'independent':
        new_h, hb = apply_batch(h, per_graph_budget, target_seed)
    else:
        new_h = h.copy()
        hb = {'inserted': [], 'deleted': []}
        # XOR-toggle the observation corresponding to each latent edit.
        # This preserves the initial observation-noise mask, even when its
        # direction differs from the source edit due to an existing flip.
        for edge in gb['inserted'] + gb['deleted']:
            u, v = sorted(int(permutation[x]) for x in edge)
            if new_h.has_edge(u, v):
                new_h.remove_edge(u, v)
                hb['deleted'].append((u, v))
            else:
                new_h.add_edge(u, v)
                hb['inserted'].append((u, v))
        hb = {name: sorted(edges) for name, edges in hb.items()}
    return new_g, new_h, gb, hb


def observation_mask(g, h, permutation):
    mapped = {tuple(sorted(int(permutation[u]) for u in edge)) for edge in g.edges()}
    observed = {tuple(sorted(edge)) for edge in h.edges()}
    return mapped ^ observed

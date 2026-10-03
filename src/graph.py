import networkx as nx
import numpy as np


def graph_pair(n, attachment, seed, noise):
    seeds = np.random.SeedSequence(seed).generate_state(4).tolist()
    g = nx.barabasi_albert_graph(n, attachment, seed=int(seeds[0]))
    permutation = np.random.default_rng(seeds[1]).permutation(n)
    h = nx.relabel_nodes(g, dict(enumerate(permutation)), copy=True)
    from .updates import apply_batch
    # Observation noise changes edges, never the hidden vertex identities.
    h, _ = apply_batch(h, round(noise * h.number_of_edges()), seeds[2])
    return g, h, permutation, seeds

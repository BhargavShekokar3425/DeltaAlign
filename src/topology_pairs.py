"""Fixed synthetic topology protocols; correspondence is generation-only."""
import networkx as nx
import numpy as np
from .updates import apply_batch


def topology_pair(n, seed, noise, family):
    if family not in {'ba','er','ws'} or n <= 6:
        raise ValueError('Expected ba/er/ws and more than six vertices')
    seeds=np.random.SeedSequence(seed).generate_state(4).tolist()
    if family=='ba':
        g=nx.barabasi_albert_graph(n,3,seed=int(seeds[0]))
    elif family=='er':
        g=nx.fast_gnp_random_graph(n,6/(n-1),seed=int(seeds[0]))
    else:
        g=nx.watts_strogatz_graph(n,6,.1,seed=int(seeds[0]))
    truth=np.random.default_rng(seeds[1]).permutation(n)
    h=nx.relabel_nodes(g,dict(enumerate(truth)),copy=True)
    h,_=apply_batch(h,round(noise*h.number_of_edges()),seeds[2])
    return g,h,truth,seeds


def statistics(graph):
    degrees=np.array([graph.degree(u) for u in range(len(graph))])
    return dict(vertices=len(graph),edges=graph.number_of_edges(),mean_degree=float(degrees.mean()),
                min_degree=int(degrees.min()),max_degree=int(degrees.max()),
                isolated_vertices=int(np.sum(degrees==0)),components=nx.number_connected_components(graph),
                mean_clustering=nx.average_clustering(graph))

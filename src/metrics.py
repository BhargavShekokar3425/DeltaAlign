import networkx as nx
import numpy as np


def quality(g, h, mapping, truth):
    conserved = sum(h.has_edge(int(mapping[u]), int(mapping[v])) for u, v in g.edges())
    union = g.number_of_edges() + h.number_of_edges() - conserved
    return {"nc": float(np.mean(mapping == truth)),
            "ec": conserved / g.number_of_edges() if g.number_of_edges() else None,
            "s3": conserved / union if union else None}


def region(before, after, batch, radius):
    seeds = {u for edge in batch['inserted'] + batch['deleted'] for u in edge}
    union = nx.compose(before, after)
    affected = set(seeds)
    frontier = set(seeds)
    for _ in range(radius):
        frontier = {v for u in frontier for v in union.neighbors(u)} - affected
        affected.update(frontier)
    return affected


def detection(affected, changed, n):
    overlap = len(affected & changed)
    return {"affected_region_size": len(affected), "repair_fraction": len(affected) / n,
            "region_recall": overlap / len(changed) if changed else None,
            "region_precision": overlap / len(affected) if affected else None}

"""Conservative dependency-local adaptations for E15; frozen kernels reused."""
from time import perf_counter
import numpy as np
from scipy.optimize import linear_sum_assignment
from src.descriptor_cache import _basic, _second, BINS, update
from experiments.e10_costs import advance as frozen_advance


def support(old,new,batch):
    endpoints={u for kind in ['inserted','deleted'] for edge in batch[kind] for u in edge}
    first=set(endpoints)
    for u in endpoints:first.update(old.neighbors(u));first.update(new.neighbors(u))
    second=set(endpoints)
    for u in first:second.update(old.neighbors(u));second.update(new.neighbors(u))
    return endpoints,first,second


def conservative_update(cache, old_graph, new_graph, batch):
    start = perf_counter()
    if len(old_graph) != len(cache.degree) or set(old_graph) != set(new_graph):
        raise ValueError('Vertex sets must stay fixed')
    endpoints = {u for kind in ['inserted', 'deleted'] for edge in batch[kind] for u in edge}
    support = set(endpoints)
    for u in endpoints:
        support.update(old_graph.neighbors(u))
        support.update(new_graph.neighbors(u))
    second_support = set(endpoints)
    for u in support:
        second_support.update(old_graph.neighbors(u))
        second_support.update(new_graph.neighbors(u))
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

def advance(context,old,new,batches,method):
    if method in ['full_scipy','persistent_scipy']:
        dirty,timings=frozen_advance(context,old,new,batches,method)
        timings['extra_support_time']=0.
        timings['rows_normalized']=[len(g) for g in new] if dirty is None else [len(d) for d in dirty]
        return dirty,timings
    start=perf_counter();extra_support_time=0.;cost_dirty=None
    if method=='conservative_costs':
        before=perf_counter()
        supports=[support(a,b,batch) for a,b,batch in zip(old,new,batches)]
        cost_dirty=[f|s for e,f,s in supports]
        extra_support_time=perf_counter()-before
    feature_start=perf_counter()
    kernel=conservative_update if method=='conservative_features' else update
    outputs=[kernel(c,a,b,batch) for c,a,b,batch in zip(context['caches'],old,new,batches)]
    features=[c.features for c in context['caches']];dirty=[d for d,s in outputs]
    feature_time=perf_counter()-feature_start
    if cost_dirty is None:cost_dirty=dirty
    cost_start=perf_counter();computed=context['cost_cache'].update(*features,*cost_dirty)
    costs=context['cost_cache'].costs;cost_time=perf_counter()-cost_start
    solver_start=perf_counter();rr,cc=linear_sum_assignment(costs)
    mapping=np.empty(len(costs),dtype=int);mapping[rr]=cc
    solver_time=perf_counter()-solver_start
    context.update(features=features,costs=costs,mapping=mapping)
    return dirty,dict(feature_time=feature_time,cost_time=cost_time,solver_time=solver_time,pipeline_time=perf_counter()-start,maintenance=[s for d,s in outputs],search_stats={},rescored_cost_entries=computed,computed_cost_entries=computed,dense_refresh_copies=0,extra_support_time=extra_support_time,rows_normalized=[len(d) for d in cost_dirty])

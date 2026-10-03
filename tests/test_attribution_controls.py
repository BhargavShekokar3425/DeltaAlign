import unittest
import networkx as nx
import numpy as np
from src.descriptors import descriptors
from src.descriptor_cache import initialize
from src.updates import apply_batch
from experiments.attribution_controls import conservative_update, support, advance
from experiments.e10_costs import setup


class AttributionTests(unittest.TestCase):
    def check_stream(self,graph,batches):
        graphs=[graph,graph.copy()]
        contexts={m:setup(graphs,'full_scipy' if m=='full_scipy' else 'persistent_scipy') for m in ['full_scipy','persistent_scipy','conservative_features','conservative_costs']}
        for batch in batches:
            new=graph.copy();new.remove_edges_from(batch['deleted']);new.add_edges_from(batch['inserted'])
            before=contexts['full_scipy']['features'][0].copy()
            outputs={m:advance(c,graphs,[new,new.copy()],[batch,batch],m) for m,c in contexts.items()}
            full=contexts['full_scipy'];dirty=set(np.flatnonzero(np.any(full['features'][0]!=before,axis=1)))
            for m,c in contexts.items():
                for f,expected in zip(c['features'],full['features']):np.testing.assert_array_equal(f,expected)
                np.testing.assert_array_equal(c['costs'],full['costs']);np.testing.assert_array_equal(c['mapping'],full['mapping'])
                if m!='full_scipy':
                    self.assertEqual(outputs[m][0],[dirty,dirty])
                    np.testing.assert_array_equal(c['cost_cache'].source,c['features'][0]/c['scale'])
                    n=len(new);a,b=outputs[m][1]['rows_normalized']
                    self.assertEqual(outputs[m][1]['computed_cost_entries'],a*n+b*(n-a))
            e,f,s=support(graph,new,batch)
            self.assertTrue(dirty<=f|s)
            self.assertEqual(outputs['conservative_features'][1]['maintenance'][0]['second_layer_support'],len(s))
            graph=new;graphs=[new,new.copy()]

    def test_no_change_overlapping_edits_bin_crossing_isolates(self):
        g=nx.star_graph(14);g.add_node(15)
        self.check_stream(g,[{'inserted':[],'deleted':[]},{'inserted':[(0,15)],'deleted':[]},{'inserted':[(1,2),(1,3)],'deleted':[(0,1),(0,2)]},{'inserted':[],'deleted':[(1,2),(1,3)]}])

    def test_repeated_mixed_and_degree_preserving_updates(self):
        for g in [nx.cycle_graph(30),nx.barabasi_albert_graph(30,3,seed=6)]:
            batches=[];working=g
            for seed in range(8):
                working,batch=apply_batch(working,4,seed,[1,0,.5][seed%3]);batches.append(batch)
            self.check_stream(g,batches)
        g=nx.cycle_graph(12)
        self.check_stream(g,[{'inserted':[(0,6),(1,7)],'deleted':[(0,1),(6,7)]}])

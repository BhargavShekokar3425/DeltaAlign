import unittest
import numpy as np
from src.graph import graph_pair
from src.update_protocols import paired_updates
from experiments.e10_costs import setup, advance


class PersistentCostStreamsTests(unittest.TestCase):
    def test_exact_persistent_graph_features_costs_and_mappings(self):
        g,h,truth,_=graph_pair(45,2,19,.05)
        for protocol in ['shared_latent','independent']:
            contexts={m:setup([g,h],m) for m in ['full_scipy','selective_scipy','persistent_scipy']}
            cache=contexts['persistent_scipy']['cost_cache']
            identity=id(cache.costs)
            old=[g,h]
            for step in range(8):
                ng,nh,gb,hb=paired_updates(*old,truth,step%5,100+step,200+step,protocol)
                for m,c in contexts.items():advance(c,old,[ng,nh],[gb,hb],m)
                full=contexts['full_scipy']
                for m in ['selective_scipy','persistent_scipy']:
                    c=contexts[m]
                    np.testing.assert_array_equal(c['costs'],full['costs'])
                    np.testing.assert_array_equal(c['mapping'],full['mapping'])
                    for actual,expected in zip(c['features'],full['features']):np.testing.assert_array_equal(actual,expected)
                np.testing.assert_array_equal(cache.source,full['features'][0]/full['scale'])
                np.testing.assert_array_equal(cache.target,full['features'][1]/full['scale'])
                self.assertEqual(id(cache.costs),identity)
                old=[ng,nh]

import unittest
import networkx as nx
import numpy as np
from scipy.spatial.distance import cdist
from scipy.optimize import linear_sum_assignment
from src.descriptor_cache import initialize
from src.descriptors import descriptors
from src.normalization import initial_scale
from src.updates import apply_batch
from experiments.e08_compiled_control import compiled_pipeline


class CompiledControlTests(unittest.TestCase):
    def test_both_sides_cost_mapping_and_cache_isolation(self):
        g = nx.barabasi_albert_graph(30, 2, seed=7)
        h = nx.barabasi_albert_graph(30, 2, seed=8)
        caches = [initialize(g), initialize(h)]
        features = [c.features.copy() for c in caches]
        scale = initial_scale(*features)
        costs = cdist(features[0]/scale, features[1]/scale, 'sqeuclidean')
        before = costs.copy()
        for budget in [0, 1, 8]:
            ng, gb = apply_batch(g,budget,10)
            nh, hb = apply_batch(h,budget,11)
            mapping, refreshed, actual, dirty, times = compiled_pipeline(costs,caches,[g,h],[ng,nh],[gb,hb],scale)
            expected = [descriptors(x,'two_hop_hist') for x in [ng,nh]]
            expected_costs = cdist(expected[0]/scale,expected[1]/scale,'sqeuclidean')
            np.testing.assert_array_equal(refreshed,expected_costs)
            np.testing.assert_array_equal(mapping,linear_sum_assignment(expected_costs)[1])
            for a,e,c,f in zip(actual,expected,caches,features):
                np.testing.assert_array_equal(a,e)
                np.testing.assert_array_equal(c.features,f)
            np.testing.assert_array_equal(costs,before)
            self.assertGreaterEqual(times['pipeline_time'],times['solver_time'])


if __name__ == '__main__':
    unittest.main()

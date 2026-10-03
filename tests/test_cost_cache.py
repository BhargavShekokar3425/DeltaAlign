import unittest
import numpy as np
from scipy.spatial.distance import cdist
from src.cost_cache import CostCache


class CostCacheTests(unittest.TestCase):
    def test_exact_blocks_all_none_overlap_and_repeated_changes(self):
        rng=np.random.default_rng(10)
        a,b=rng.integers(-4,5,size=(2,15,7)).astype(float)
        scale=np.arange(1,8)/3
        cache=CostCache.initialize(a,b,scale)
        identity=id(cache.costs)
        for rows,cols in [(set(),set()),({1,4},set()),(set(),{0,4}),({1,2,3},{2,3,4}),
                          (set(range(15)),{1,4}),({2,3},set(range(15)))]+[({i%15},{(i+3)%15}) for i in range(20)]:
            a[list(rows)]+=rng.normal(size=(len(rows),7))
            b[list(cols)]+=rng.normal(size=(len(cols),7))
            count=cache.update(a,b,rows,cols)
            np.testing.assert_array_equal(cache.source,a/scale)
            np.testing.assert_array_equal(cache.target,b/scale)
            np.testing.assert_array_equal(cache.costs,cdist(a/scale,b/scale,'sqeuclidean'))
            self.assertEqual(count,len(rows)*15+len(cols)*(15-len(rows)))
            self.assertEqual(id(cache.costs),identity)
        with self.assertRaises(ValueError):cache.update(a,b,{15},set())
        with self.assertRaises(ValueError):CostCache.initialize(a,b,np.zeros(7))

    def test_ties_and_scale_ownership(self):
        a=np.ones((4,3));scale=np.ones(3)
        cache=CostCache.initialize(a,a.copy(),scale)
        scale[0]=10
        np.testing.assert_array_equal(cache.scale,np.ones(3))
        cache.update(a,a,set(range(4)),set(range(4)))
        np.testing.assert_array_equal(cache.costs,np.zeros((4,4)))

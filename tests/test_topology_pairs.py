import unittest
import numpy as np
from src.topology_pairs import topology_pair,statistics
from src.graph import graph_pair
from src.update_protocols import observation_mask


class TopologyPairTests(unittest.TestCase):
    def test_permutation_noise_and_reproducibility(self):
        for family in ['ba','er','ws']:
            g,h,truth,seeds=topology_pair(40,55,0,family)
            self.assertEqual(observation_mask(g,h,truth),set())
            gg,hh,tt,ss=topology_pair(40,55,.05,family)
            g2,h2,t2,s2=topology_pair(40,55,.05,family)
            self.assertEqual(set(gg.edges()),set(g2.edges()))
            self.assertEqual(set(hh.edges()),set(h2.edges()))
            np.testing.assert_array_equal(tt,t2)
            self.assertEqual(ss,s2)
            self.assertEqual(len(observation_mask(gg,hh,tt)),round(.05*gg.number_of_edges()))
            self.assertEqual(set(gg),set(range(40)))
            self.assertEqual(statistics(gg)['vertices'],40)
        a=topology_pair(40,55,.05,'ba');b=graph_pair(40,3,55,.05)
        self.assertEqual(set(a[0].edges()),set(b[0].edges()))
        self.assertEqual(set(a[1].edges()),set(b[1].edges()))
        np.testing.assert_array_equal(a[2],b[2])
        with self.assertRaises(ValueError):topology_pair(40,1,0,'bad')

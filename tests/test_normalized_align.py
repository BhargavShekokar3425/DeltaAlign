import unittest
import numpy as np
from src.graph import graph_pair
from src.normalized_align import full_align
from src.descriptors import descriptors
from src.normalization import initial_scale


class CorrectedAlignmentTests(unittest.TestCase):
    def test_default_uses_corrected_scale_and_updates_freeze_it(self):
        g, h, _, _ = graph_pair(40, 3, 3, 0)
        mapping, scale, stats = full_align(g, h, descriptor_mode='two_hop_hist')
        np.testing.assert_array_equal(scale, initial_scale(descriptors(g, 'two_hop_hist'), descriptors(h, 'two_hop_hist')))
        self.assertEqual(len(set(mapping)), 40)
        self.assertAlmostEqual(stats['objective'], 0.)
        h.remove_edge(*next(iter(h.edges())))
        _, frozen, _ = full_align(g, h, scale=scale, descriptor_mode='two_hop_hist')
        np.testing.assert_array_equal(scale, frozen)
        self.assertGreaterEqual(stats['runtime'], stats['normalization_time'])

    def test_rejects_invalid_supplied_scale(self):
        g, h, _, _ = graph_pair(10, 3, 1, 0)
        for scale in [np.array([1., 0., 1.]), np.array([1., np.nan, 1.])]:
            with self.assertRaises(ValueError):
                full_align(g, h, scale=scale)

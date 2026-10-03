import unittest
import numpy as np
from scipy.spatial.distance import cdist
from src.normalization import initial_scale
from src.graph import graph_pair
from src.descriptors import descriptors
from src.full_align import full_align


class NormalizationTests(unittest.TestCase):
    def test_newly_active_bin_has_finite_unit_cost(self):
        source = np.array([[0., 0.], [2., 0.]])
        scale = initial_scale(source, source)
        np.testing.assert_array_equal(scale, [1., 1.])
        updated = source.copy()
        updated[0, 1] = 1.
        self.assertEqual(cdist(updated/scale, source/scale, 'sqeuclidean')[0, 0], 1.)
        legacy = np.maximum(np.vstack([source, source]).std(axis=0), 1e-12)
        self.assertGreater(cdist(updated/legacy, source/legacy, 'sqeuclidean')[0, 0], 1e20)

    def test_scale_is_pooled_and_permutation_invariant(self):
        a = np.array([[0., 1., 2.], [2., 1., 4.], [3., 1., 8.]])
        b = a + np.array([1., 0., 0.])
        expected = np.vstack([a, b]).std(axis=0)
        expected[1] = 1.
        np.testing.assert_allclose(initial_scale(a, b), expected)
        np.testing.assert_allclose(initial_scale(a[::-1], b[[1, 2, 0]]), expected)

    def test_noiseless_graph_and_frozen_updated_scale(self):
        g, h, truth, _ = graph_pair(80, 3, 42, 0)
        fg, fh = descriptors(g, 'two_hop_hist'), descriptors(h, 'two_hop_hist')
        scale = initial_scale(fg, fh)
        old, returned, stats = full_align(g, h, scale=scale, descriptor_mode='two_hop_hist')
        np.testing.assert_array_equal(returned, scale)
        self.assertAlmostEqual(stats['objective'], 0.)
        h.add_edge(0, 79)
        _, updated_scale, _ = full_align(g, h, scale=scale, descriptor_mode='two_hop_hist')
        np.testing.assert_array_equal(updated_scale, scale)
        self.assertEqual(len(set(old)), 80)

    def test_bad_inputs_and_tolerance(self):
        for features in [np.array([[np.nan]]), np.empty((0, 1))]:
            with self.assertRaises(ValueError):
                initial_scale(features, features)
        with self.assertRaises(ValueError):
            initial_scale(np.zeros((2, 1)), np.zeros((2, 2)))
        scale = initial_scale(np.array([[0., 1e-14], [1., 0.]]), np.zeros((2, 2)))
        self.assertEqual(scale[1], 1.)

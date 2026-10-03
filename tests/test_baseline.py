import itertools
import unittest
import networkx as nx
import numpy as np
from scipy.optimize import linear_sum_assignment
from src.graph import graph_pair
from src.updates import apply_batch
from src.full_align import full_align
from src.metrics import quality, detection, region
from src.descriptors import descriptors


class BaselineTests(unittest.TestCase):
    def test_stronger_descriptors_are_permutation_equivariant(self):
        g, h, truth, _ = graph_pair(40, 3, 8, 0)
        for mode in ["degree_hist", "two_hop_hist"]:
            np.testing.assert_allclose(descriptors(g, mode), descriptors(h, mode)[truth])
            mapping, _, stats = full_align(g, h, descriptor_mode=mode)
            self.assertEqual(len(set(mapping)), 40)
            self.assertAlmostEqual(stats['objective'], 0)

    def test_neighbor_iteration_order_is_exactly_invariant(self):
        g, _, _, _ = graph_pair(80, 3, 9, 0)
        reordered = nx.Graph()
        reordered.add_nodes_from(range(80))
        reordered.add_edges_from(reversed(list(g.edges())))
        for mode in ["basic", "degree_hist", "two_hop_hist"]:
            np.testing.assert_array_equal(descriptors(g, mode), descriptors(reordered, mode))

    def test_descriptor_update_support(self):
        g = nx.path_graph(8)
        h = g.copy()
        h.add_edge(0, 2)
        batch = {'inserted': [(0, 2)], 'deleted': []}
        for mode, radius in [("basic", 1), ("degree_hist", 1), ("two_hop_hist", 2)]:
            changed = set(np.flatnonzero(np.any(descriptors(g, mode) != descriptors(h, mode), axis=1)))
            self.assertTrue(changed <= region(g, h, batch, radius))

    def test_assignment_against_enumeration(self):
        costs = np.array([[8, 2, 5], [3, 9, 4], [6, 7, 1]])
        rows, cols = linear_sum_assignment(costs)
        exhaustive = min(sum(costs[u, v] for u, v in enumerate(p)) for p in itertools.permutations(range(3)))
        self.assertEqual(costs[rows, cols].sum(), exhaustive)

    def test_graph_identity_and_updates(self):
        g, h, truth, _ = graph_pair(30, 3, 4, 0)
        self.assertTrue(all(h.has_edge(int(truth[u]), int(truth[v])) for u, v in g.edges()))
        updated, batch = apply_batch(g, 11, 9)
        self.assertEqual(len(set(g.edges()) ^ set(updated.edges())), 11)
        self.assertEqual(len(batch['inserted']) + len(batch['deleted']), 11)
        self.assertEqual(set(g), set(updated))
        self.assertEqual(nx.number_of_selfloops(updated), 0)

    def test_quality_and_deleted_endpoint_region(self):
        g = nx.path_graph(3)
        self.assertEqual(quality(g, g, np.arange(3), np.arange(3)), {'nc': 1., 'ec': 1., 's3': 1.})
        h = g.copy()
        h.remove_edge(0, 1)
        self.assertEqual(region(g, h, {'inserted': [], 'deleted': [(0, 1)]}, 1), {0, 1, 2})
        self.assertIsNone(detection({0}, set(), 3)['region_recall'])

    def test_noiseless_objective_and_determinism(self):
        g, h, truth, _ = graph_pair(40, 3, 1, 0)
        mapping, scale, stats = full_align(g, h)
        other, _, _ = full_align(g, h, scale)
        self.assertTrue(np.array_equal(mapping, other))
        self.assertEqual(len(set(mapping)), 40)
        self.assertAlmostEqual(stats['objective'], 0)


if __name__ == '__main__':
    unittest.main()

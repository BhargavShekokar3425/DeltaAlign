import unittest
import numpy as np
from scipy.spatial.distance import cdist
from src.candidates import candidate_lists, refresh_costs, update_candidates, dependency_seeds
from src.conflict_closure import conflict_closure


class DetectionTests(unittest.TestCase):
    def test_new_target_enters_without_old_reverse_dependency(self):
        mapping = np.arange(3)
        old_cost = np.array([[0., 2., 8.], [4., 0., 8.], [8., 3., 0.]])
        old = candidate_lists(old_cost, mapping, 1)
        new_cost = old_cost.copy()
        new_cost[0, 2] = -1
        new, dirty = update_candidates(old, new_cost, set(), {2}, mapping, 1)
        self.assertEqual(new, candidate_lists(new_cost, mapping, 1))
        self.assertEqual(dirty, {0, 1, 2})
        self.assertIn(0, dependency_seeds(set(), {2}, mapping, old, new))
        self.assertIn(0, new[0])  # Old-match feasibility edge remains.
        self.assertIn(2, new[0])

    def test_closure_chain_and_frozen_target_separation(self):
        mapping = np.array([2, 0, 3, 1])
        candidates = [{2, 0}, {0, 3}, {3}, {1}]
        affected, stats = conflict_closure({0}, candidates, mapping)
        self.assertEqual(affected, {0, 1, 2})
        self.assertEqual(stats['closure_added'], 2)
        self.assertEqual(stats['closure_depth'], 2)
        self.assertEqual(conflict_closure(set(), candidates, mapping)[0], set())

    def test_exact_cost_and_candidate_refresh(self):
        rng = np.random.default_rng(42)
        source, target = rng.random((7, 3)), rng.random((7, 3))
        mapping, scale = np.arange(7), np.array([1., 2., 3.])
        costs = cdist(source / scale, target / scale, 'sqeuclidean')
        new_source, new_target = source.copy(), target.copy()
        new_source[1] += .4
        new_target[3] -= .2
        refreshed, work = refresh_costs(costs, new_source, new_target, {1}, {3}, scale)
        reference = cdist(new_source / scale, new_target / scale, 'sqeuclidean')
        np.testing.assert_array_equal(refreshed, reference)
        self.assertEqual(work, 13)
        for k in [1, 3, 7]:
            old = candidate_lists(costs, mapping, k)
            new, _ = update_candidates(old, refreshed, {1}, {3}, mapping, k)
            self.assertEqual(new, candidate_lists(reference, mapping, k))

    def test_stable_ties_and_source_only_refresh(self):
        costs, mapping = np.zeros((4, 4)), np.arange(4)
        old = candidate_lists(costs, mapping, 1)
        self.assertEqual(old[3], {0, 3})
        changed = costs.copy()
        changed[2, 1] = -1
        new, dirty = update_candidates(old, changed, {2}, set(), mapping, 1)
        self.assertEqual(dirty, {2})
        self.assertEqual(new, candidate_lists(changed, mapping, 1))

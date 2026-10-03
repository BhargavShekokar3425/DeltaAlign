import itertools
import unittest
import numpy as np
from src.local_assignment import restricted_assignment
from src.repair_metrics import fidelity, objective


class LocalAssignmentTests(unittest.TestCase):
    def test_masked_assignment_against_exhaustive_feasible_maps(self):
        costs = np.array([[9., 1., 4., 0.], [1., 8., 3., 0.], [4., 2., 0., 0.], [0., 0., 0., 1.]])
        old = np.arange(4)
        affected = {0, 1, 2}
        candidates = [{0, 1}, {0, 1, 2}, {1, 2}, {3}]
        mapping, stats = restricted_assignment(costs, old, affected, candidates)
        feasible = []
        for p in itertools.permutations(range(3)):
            if all(p[u] in candidates[u] for u in range(3)):
                trial = np.array([*p, 3])
                feasible.append(objective(costs, trial))
        self.assertEqual(objective(costs, mapping), min(feasible))
        self.assertEqual(mapping[3], 3)
        self.assertEqual(stats['repair_size'], 3)

    def test_nonidentity_old_image_and_dense_ablation(self):
        costs = np.array([[3., 0., 9.], [0., 2., 9.], [9., 9., 0.]])
        old = np.array([1, 0, 2])
        result, _ = restricted_assignment(costs, old, {0, 1})
        np.testing.assert_array_equal(result, old)
        none, _ = restricted_assignment(costs, old, set())
        np.testing.assert_array_equal(none, old)

    def test_rejects_escaping_or_missing_old_candidates(self):
        costs, old = np.zeros((3, 3)), np.arange(3)
        with self.assertRaises(ValueError):
            restricted_assignment(costs, old, {0}, [{0, 1}, {1}, {2}])
        with self.assertRaises(ValueError):
            restricted_assignment(costs, old, {0, 1}, [{1}, {0, 1}, {2}])

    def test_pruning_and_region_losses_add_to_full_gap(self):
        costs = np.array([[3., 0., 9.], [0., 3., 9.], [9., 9., 0.]])
        old, full = np.arange(3), np.array([1, 0, 2])
        pruned, _ = restricted_assignment(costs, old, {0, 1}, [{0}, {1}, {2}])
        dense, _ = restricted_assignment(costs, old, {0, 1})
        self.assertEqual(objective(costs, pruned)-objective(costs, dense), 6.)
        stats = fidelity(costs, pruned, full, old)
        self.assertEqual(stats['absolute_objective_gap'], 6.)
        self.assertIsNone(stats['relative_objective_gap'])
        self.assertEqual(stats['objective_gain_recovered'], 0.)
        self.assertEqual(fidelity(costs, dense, full, old)['objective_gain_recovered'], 1.)

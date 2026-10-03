import unittest
import numpy as np
from src.candidate_pruning import (ranked_targets, refresh_rankings, pruned_candidates,
                                  refresh_pruned_candidates, confidence_seeds)
from src.conflict_closure import conflict_closure


class PruningTests(unittest.TestCase):
    def test_margin_includes_old_match_and_boundaries(self):
        costs = np.array([[0., .2, 4.], [.3, 0., .6], [4., .3, 0.]])
        mapping = np.array([2, 1, 0])
        lists = pruned_candidates(costs, mapping, 3, .1, 2)
        self.assertEqual(lists[0], {0, 1, 2})
        self.assertEqual(lists[1], {1})
        self.assertEqual(lists[2], {0, 2})
        closed, _ = conflict_closure({0}, lists, mapping)
        self.assertTrue(all(lists[u] <= {int(mapping[x]) for x in closed} for u in closed))

    def test_new_target_entrant_refresh(self):
        costs = np.array([[0., 1., 4.], [2., 0., 4.], [3., 2., 0.]])
        mapping = np.arange(3)
        old_rank = ranked_targets(costs, 3)
        old = pruned_candidates(costs, mapping, 2, .1, 1, old_rank)
        new_cost = costs.copy()
        new_cost[0, 2] = -.5
        rankings, dirty = refresh_rankings(old_rank, new_cost, set(), {2})
        np.testing.assert_array_equal(rankings, ranked_targets(new_cost, 3))
        new = refresh_pruned_candidates(old, new_cost, mapping, 2, .1, 1, rankings, dirty)
        self.assertEqual(new, pruned_candidates(new_cost, mapping, 2, .1, 1))
        self.assertEqual(new[0], {0, 2})

    def test_confidence_threshold_and_no_pressure(self):
        old = np.array([[0., 2.], [2., 0.]])
        new = np.array([[1., 0.], [2., 0.]])
        selected, pressure = confidence_seeds({0, 1}, old, new, np.arange(2), 2, .4)
        self.assertEqual(selected, {0})
        self.assertEqual(pressure.tolist(), [.5, 0.])
        self.assertEqual(confidence_seeds({0, 1}, old, new, np.arange(2), 2, .5)[0], set())

    def test_source_only_refresh_and_zero_margin_ties(self):
        costs = np.zeros((4, 4))
        mapping = np.arange(4)
        rank = ranked_targets(costs, 2)
        old = pruned_candidates(costs, mapping, 2, 0, 1, rank)
        costs[2, 1] = -1
        new_rank, dirty = refresh_rankings(rank, costs, {2}, set())
        self.assertEqual(dirty, {2})
        refreshed = refresh_pruned_candidates(old, costs, mapping, 2, 0, 1, new_rank, dirty)
        self.assertEqual(refreshed, pruned_candidates(costs, mapping, 2, 0, 1))
        self.assertEqual(refreshed[2], {1, 2})

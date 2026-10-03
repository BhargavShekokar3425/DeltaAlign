import itertools
import unittest
import numpy as np
from scipy.optimize import linear_sum_assignment
from src.dynamic_assignment import solve, repair, certificate


class DynamicAssignmentTests(unittest.TestCase):
    def assert_optimal(self, state):
        r, c = linear_sum_assignment(state.costs)
        self.assertAlmostEqual(state.costs[np.arange(len(c)),state.mapping].sum(), state.costs[r,c].sum(), places=7)
        self.assertTrue(certificate(state)['certificate_passed'])

    def test_signed_tied_and_exhaustive_small_assignments(self):
        rng = np.random.default_rng(8)
        for n in range(1,7):
            for _ in range(5):
                costs = rng.integers(-5,6,(n,n)).astype(float)
                state, _ = solve(costs)
                best = min(sum(costs[u,v] for u,v in enumerate(p)) for p in itertools.permutations(range(n)))
                self.assertAlmostEqual(state.costs[np.arange(n),state.mapping].sum(), best)
                self.assert_optimal(state)

    def test_row_column_mixed_all_and_no_changes(self):
        rng = np.random.default_rng(12)
        for n in [3,8,20]:
            for mode in ['row','column','mixed','all','none']:
                costs = rng.normal(size=(n,n))
                state, _ = solve(costs)
                new = costs.copy()
                rows = {0,1} if mode in ['row','mixed'] else (set(range(n)) if mode=='all' else set())
                columns = {1,2} if mode in ['column','mixed'] else set()
                for u in rows: new[u] = rng.normal(size=n)
                for v in columns: new[:,v] = rng.normal(size=n)
                state, stats = repair(state,new,rows,columns)
                self.assert_optimal(state)
                self.assertLessEqual(stats['augmentations'],len(rows)+len(columns))
                if mode=='none': self.assertEqual(stats['augmentations'],0)

    def test_repeated_updates_preserve_certificate(self):
        rng = np.random.default_rng(42)
        state, _ = solve(rng.random((12,12)))
        for _ in range(30):
            new = state.costs.copy()
            row,column = int(rng.integers(12)),int(rng.integers(12))
            new[row] = rng.random(12)*10
            new[:,column] = rng.random(12)*10
            state,_ = repair(state,new,{row},{column})
            self.assert_optimal(state)

    def test_copy_isolated_and_bad_inputs(self):
        state,_=solve(np.eye(3))
        clone=state.copy()
        clone.row_dual[0]=9
        self.assertNotEqual(state.row_dual[0],clone.row_dual[0])
        with self.assertRaises(ValueError): solve(np.array([[np.inf]]))
        with self.assertRaises(ValueError): repair(state,np.eye(3),{3},set())

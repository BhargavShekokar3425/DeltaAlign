"""Primal-dual dynamic Hungarian reference; original implementation.

Based on the dual-feasibility/unmatch/augment construction in CMU-RI-TR-07-27,
Figure 5 and its batch extension. Trees use deterministic single-root stages.
This is a Python/NumPy reference, not the authors' code or a new algorithm.
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class AssignmentState:
    costs: np.ndarray
    mapping: np.ndarray
    inverse: np.ndarray
    row_dual: np.ndarray
    column_dual: np.ndarray

    def copy(self):
        return AssignmentState(*(array.copy() for array in
            [self.costs, self.mapping, self.inverse, self.row_dual, self.column_dual]))


def _validate_costs(costs):
    costs = np.asarray(costs, dtype=float)
    if costs.ndim != 2 or costs.shape[0] != costs.shape[1] or not len(costs) or not np.isfinite(costs).all():
        raise ValueError('Expected a finite nonempty square cost matrix')
    return costs


def _augment(state, root, stats):
    n = len(state.mapping)
    seen_rows = np.zeros(n, dtype=bool)
    seen_columns = np.zeros(n, dtype=bool)
    slack = np.full(n, np.inf)
    predecessor = np.full(n, -1, dtype=int)
    row = root
    while True:
        seen_rows[row] = True
        stats['rows_visited'].add(int(row))
        stats['tree_steps'] += 1
        stats['cost_cells_examined'] += n
        reduced = state.costs[row] - state.row_dual[row] - state.column_dual
        improves = (~seen_columns) & (reduced < slack)
        slack[improves] = reduced[improves]
        predecessor[improves] = row
        available = np.where(seen_columns, np.inf, slack)
        column = int(np.argmin(available))
        delta = float(available[column])
        if not np.isfinite(delta):
            raise RuntimeError('No augmenting path')
        tolerance = 1e-10 * max(1., float(np.max(np.abs(state.costs[row]))))
        if delta < -tolerance:
            raise RuntimeError('Dual feasibility violated before augmentation')
        delta = max(0., delta)
        state.row_dual[seen_rows] += delta
        state.column_dual[seen_columns] -= delta
        slack[~seen_columns] -= delta
        seen_columns[column] = True
        stats['columns_visited'].add(column)
        next_row = int(state.inverse[column])
        if next_row == -1:
            # Flip the entire alternating path, including formerly matched rows.
            while column != -1:
                row = int(predecessor[column])
                previous = int(state.mapping[row])
                state.mapping[row] = column
                state.inverse[column] = row
                column = previous
            break
        row = next_row


def _complete(state):
    stats = {'augmentations': 0, 'tree_steps': 0, 'cost_cells_examined': 0,
             'rows_visited': set(), 'columns_visited': set()}
    for row in np.flatnonzero(state.mapping < 0):
        _augment(state, int(row), stats)
        stats['augmentations'] += 1
    stats['visited_rows'] = len(stats.pop('rows_visited'))
    stats['visited_columns'] = len(stats.pop('columns_visited'))
    return stats


def solve(costs):
    costs = _validate_costs(costs).copy()
    n = len(costs)
    state = AssignmentState(costs, np.full(n, -1, dtype=int), np.full(n, -1, dtype=int),
                            costs.min(axis=1), np.zeros(n))
    stats = _complete(state)
    return state, stats


def repair(state, new_costs, changed_rows, changed_columns):
    costs = _validate_costs(new_costs)
    n = len(state.mapping)
    rows, columns = sorted(set(changed_rows)), sorted(set(changed_columns))
    if costs.shape != state.costs.shape or not set(rows+columns) <= set(range(n)):
        raise ValueError('Invalid changed cost region')
    affected = set(rows) | {int(state.inverse[j]) for j in columns}
    for row in sorted(affected):
        column = int(state.mapping[row])
        state.mapping[row] = -1
        state.inverse[column] = -1
    # Reset columns against unchanged row potentials first; reset affected
    # rows afterward. This ensures feasibility for simultaneous row/column edits.
    unchanged_rows = sorted(set(range(n))-set(rows))
    for column in columns:
        state.column_dual[column] = (np.min(costs[unchanged_rows, column]-state.row_dual[unchanged_rows])
                                     if unchanged_rows else 0.)
    for row in rows:
        state.row_dual[row] = np.min(costs[row]-state.column_dual)
    state.costs = costs.copy()
    stats = _complete(state)
    stats.update({'initially_exposed_rows': len(affected), 'changed_rows': len(rows), 'changed_columns': len(columns)})
    return state, stats


def certificate(state, tolerance=1e-8):
    n = len(state.mapping)
    if set(state.mapping) != set(range(n)) or not np.array_equal(state.inverse[state.mapping], np.arange(n)):
        raise RuntimeError('Invalid primal permutation/inverse')
    reduced = state.costs-state.row_dual[:, None]-state.column_dual[None, :]
    error = float(np.max(np.abs(reduced[np.arange(n), state.mapping])))
    violation = float(max(0., -reduced.min()))
    primal = float(state.costs[np.arange(n), state.mapping].sum())
    dual = float(state.row_dual.sum()+state.column_dual.sum())
    if violation > tolerance or error > tolerance or abs(primal-dual) > tolerance*max(1., abs(primal)):
        raise RuntimeError('Primal-dual optimality certificate failed')
    return {'dual_feasibility_violation': violation, 'matched_edge_slack': error,
            'primal_dual_gap': abs(primal-dual), 'certificate_passed': True}

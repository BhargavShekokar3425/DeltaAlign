import unittest
import networkx as nx
import numpy as np
from src.descriptors import descriptors
from src.descriptor_cache import initialize, update
from src.updates import apply_batch


class DescriptorCacheTests(unittest.TestCase):
    def check_update(self, graph, cache, new_graph, batch):
        before = cache.features.copy()
        changed, stats = update(cache, graph, new_graph, batch)
        expected = descriptors(new_graph, 'two_hop_hist')
        np.testing.assert_array_equal(cache.features, expected)
        self.assertEqual(changed, set(np.flatnonzero(np.any(expected != before, axis=1))))
        self.assertLessEqual(len(changed), stats['total_support'])

    def test_repeated_insert_delete_mixed_and_hubs(self):
        for graph in [nx.empty_graph(40), nx.star_graph(39), nx.barabasi_albert_graph(40, 3, seed=4)]:
            cache = initialize(graph)
            np.testing.assert_array_equal(cache.features, descriptors(graph, 'two_hop_hist'))
            for seed in range(12):
                fraction = [1., 0., .5][seed % 3]
                if 4-int(4*fraction+.5) > graph.number_of_edges():
                    fraction = 1.
                new_graph, batch = apply_batch(graph, 4, seed, fraction)
                self.check_update(graph, cache, new_graph, batch)
                graph = new_graph

    def test_bin_changes_and_adjacency_changes(self):
        graph = nx.star_graph(14)
        graph.add_node(15)
        cache = initialize(graph)
        new_graph = graph.copy()
        new_graph.add_edge(0, 15)  # hub crosses fixed degree bin 15
        self.check_update(graph, cache, new_graph, {'inserted': [(0,15)], 'deleted': []})
        graph = new_graph
        new_graph = graph.copy()
        new_graph.remove_edge(0, 1)
        new_graph.add_edge(1, 2)
        self.check_update(graph, cache, new_graph, {'inserted': [(1,2)], 'deleted': [(0,1)]})

    def test_no_update_clone_and_invalid_vertices(self):
        graph = nx.path_graph(10)
        cache = initialize(graph)
        clone = cache.copy()
        self.check_update(graph, clone, graph.copy(), {'inserted': [], 'deleted': []})
        clone.features[0,0] += 1
        self.assertNotEqual(clone.features[0,0], cache.features[0,0])
        with self.assertRaises(ValueError):
            initialize(nx.path_graph(['a','b']))
        with self.assertRaises(ValueError):
            update(cache, graph, nx.path_graph(11), {'inserted': [], 'deleted': []})


if __name__ == '__main__':
    unittest.main()

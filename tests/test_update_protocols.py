import unittest
from src.graph import graph_pair
from src.update_protocols import paired_updates, observation_mask


class UpdateProtocolTests(unittest.TestCase):
    def test_persistent_noise_mask_and_balanced_effective_counts(self):
        g, h, permutation, seeds = graph_pair(50, 3, 12, .05)
        before = observation_mask(g, h, permutation)
        ng, nh, gb, hb = paired_updates(g, h, permutation, 9, seeds[3], 10, 'shared_latent')
        self.assertEqual(before, observation_mask(ng, nh, permutation))
        self.assertEqual(sum(map(len, gb.values())), 9)
        self.assertEqual(sum(map(len, hb.values())), 9)
        self.assertEqual(set(g), set(ng))
        self.assertEqual(set(h), set(nh))

    def test_noise_flip_reverses_observed_edit_direction(self):
        g, h, permutation, seeds = graph_pair(20, 3, 2, 0)
        # Discover the deterministic latent insertion and pre-flip it in H.
        _, _, gb, _ = paired_updates(g, h, permutation, 1, 7, 9, 'shared_latent')
        edge = tuple(sorted(int(permutation[u]) for u in gb['inserted'][0]))
        h.add_edge(*edge)
        mask = observation_mask(g, h, permutation)
        ng, nh, _, hb = paired_updates(g, h, permutation, 1, 7, 9, 'shared_latent')
        self.assertEqual(hb['deleted'], [edge])
        self.assertEqual(mask, observation_mask(ng, nh, permutation))

    def test_protocols_share_source_batch_and_initial_state_is_untouched(self):
        g, h, permutation, seeds = graph_pair(30, 3, 4, .05)
        original = set(g.edges()), set(h.edges())
        a = paired_updates(g, h, permutation, 4, seeds[3], 10, 'shared_latent')
        b = paired_updates(g, h, permutation, 4, seeds[3], 10, 'independent')
        self.assertEqual(set(a[0].edges()), set(b[0].edges()))
        self.assertEqual(a[2], b[2])
        self.assertEqual(original, (set(g.edges()), set(h.edges())))
        self.assertEqual(sum(map(len, b[3].values())), 4)

    def test_zero_updates_and_invalid_protocol(self):
        g, h, permutation, _ = graph_pair(20, 3, 1, 0)
        ng, nh, _, _ = paired_updates(g, h, permutation, 0, 1, 2, 'shared_latent')
        self.assertEqual(set(g.edges()), set(ng.edges()))
        self.assertEqual(set(h.edges()), set(nh.edges()))
        with self.assertRaises(ValueError):
            paired_updates(g, h, permutation, 1, 1, 2, 'unknown')

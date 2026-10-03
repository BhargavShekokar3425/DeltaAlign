import unittest
import numpy as np
from src.graph import graph_pair
from src.update_protocols import paired_updates, observation_mask
from src.dynamic_assignment import certificate
from experiments.e09_streams import setup, advance


class StreamTests(unittest.TestCase):
    def test_persistent_costs_features_duals_and_protocols(self):
        g,h,truth,_=graph_pair(35,2,7,.05)
        for protocol in ['shared_latent','independent']:
            contexts={m:setup([g,h],m) for m in ['full_scipy','selective_scipy','selective_dynamic']}
            old=[g,h]
            mask=observation_mask(g,h,truth)
            scale=contexts['full_scipy']['scale'].copy()
            cache_ids=[id(x) for x in contexts['selective_dynamic']['caches']]
            state_id=id(contexts['selective_dynamic']['state'])
            for step in range(8):
                ng,nh,gb,hb=paired_updates(*old,truth,3,100+step,200+step,protocol)
                for m,c in contexts.items():
                    advance(c,old,[ng,nh],[gb,hb],m)
                    np.testing.assert_array_equal(c['scale'],scale)
                full=contexts['full_scipy']
                for m in ['selective_dynamic','selective_scipy']:
                    c=contexts[m]
                    np.testing.assert_array_equal(c['costs'],full['costs'])
                    for f,e in zip(c['features'],full['features']):np.testing.assert_array_equal(f,e)
                    actual=c['costs'][np.arange(35),c['mapping']].sum()
                    expected=full['costs'][np.arange(35),full['mapping']].sum()
                    self.assertAlmostEqual(actual,expected,places=8)
                np.testing.assert_array_equal(contexts['selective_scipy']['mapping'],full['mapping'])
                certificate(contexts['selective_dynamic']['state'])
                if protocol=='shared_latent':self.assertEqual(observation_mask(ng,nh,truth),mask)
                old=[ng,nh]
            self.assertEqual([id(x) for x in contexts['selective_dynamic']['caches']],cache_ids)
            self.assertEqual(id(contexts['selective_dynamic']['state']),state_id)


if __name__=='__main__':unittest.main()

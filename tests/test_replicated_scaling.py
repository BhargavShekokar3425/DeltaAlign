import contextlib
import io
import json
import unittest
from experiments.e13_scaling import worker


class ReplicatedScalingTests(unittest.TestCase):
    def test_fresh_seed_exactness_and_seed_selection(self):
        initial=[]
        for seed in [61,62]:
            for family in ['ba','er','ws']:
                pair=[]
                for method in ['full_scipy','persistent_scipy']:
                    output=io.StringIO()
                    with contextlib.redirect_stdout(output):worker(35,family,method,seed)
                    result=json.loads(output.getvalue())
                    self.assertEqual(result['seed'],seed)
                    self.assertEqual(len(result['records']),4)
                    pair.append(result)
                for a,b in zip(pair[0]['records'],pair[1]['records']):
                    self.assertEqual(a['hashes'],b['hashes'])
                    self.assertEqual(a['objective'],b['objective'])
                if family=='ba':initial.append(pair[0]['records'][0]['hashes']['features'])
        self.assertNotEqual(*initial)

import contextlib
import io
import json
import unittest
import numpy as np
from experiments.e12_resources import worker,fingerprint,headroom


class ResourceProfileTests(unittest.TestCase):
    def test_worker_fingerprints_match_with_full_cost_release(self):
        for family in ['ba','er','ws']:
            records=[]
            for method in ['full_scipy','persistent_scipy']:
                output=io.StringIO()
                with contextlib.redirect_stdout(output):worker(35,family,method)
                records.append(json.loads(output.getvalue()))
            for a,b in zip(records[0]['records'],records[1]['records']):
                self.assertEqual(a['hashes'],b['hashes'])
                self.assertEqual(a['objective'],b['objective'])
        with self.assertRaises(ValueError):fingerprint(np.zeros((5,5))[:,::2])
        self.assertGreater(headroom()['effective_available_bytes'],0)

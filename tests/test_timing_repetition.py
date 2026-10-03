import copy
import unittest
from experiments.e16_timing import validate


class TimingRepetitionTests(unittest.TestCase):
    def test_validation_rejects_historical_and_paired_drift(self):
        record={'records':[{'step':step,'hashes':{'features':['a','b'],'costs':'c','mapping':'d'},'objective':3.} for step in range(4)]}
        validate(record,copy.deepcopy(record))
        for field,value in [('hashes',{'costs':'different'}),('objective',4.),('step',99)]:
            changed=copy.deepcopy(record);changed['records'][2][field]=value
            with self.assertRaises(AssertionError):validate(changed,record)
        with self.assertRaises(AssertionError):validate({'records':record['records'][:-1]},record)

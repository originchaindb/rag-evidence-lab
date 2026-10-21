import copy
import json
from pathlib import Path
import unittest
from logic import evaluate

class LogicTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(Path('examples/input.json').read_text())
    def test_wrong_claim_with_valid_citation(self):
        r=evaluate(self.data); self.assertTrue(r['cases'][0]['passed']); self.assertFalse(r['cases'][1]['passed']); self.assertTrue(r['cases'][2]['passed'])
    def test_unknown_and_fabricated_quote(self):
        c=self.data['cases'][0]; c['citations'][0]['document_id']='missing'
        self.assertIn('unknown_citation',evaluate(self.data)['cases'][0]['reasons'])
        c['citations'][0]={'document_id':'refund','quote':'90 days'}
        self.assertIn('quote_not_in_document',evaluate(self.data)['cases'][0]['reasons'])
    def test_abstention(self):
        self.data['cases'][2]['abstained']=False
        self.assertIn('should_abstain',evaluate(self.data)['cases'][2]['reasons'])
    def test_duplicate_and_empty_cases(self):
        self.data['cases'].append(self.data['cases'][0])
        with self.assertRaises(ValueError): evaluate(self.data)
        self.data['cases']=[]
        with self.assertRaises(ValueError): evaluate(self.data)

if __name__=='__main__': unittest.main()

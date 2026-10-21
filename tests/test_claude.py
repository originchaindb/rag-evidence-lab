import json
import os
from pathlib import Path
import tempfile
from unittest import TestCase
from claude_capture import parse_response, reserve

class ClaudeTests(TestCase):
    def test_parses_only_completed_json(self):
        r=parse_response(json.dumps({'stop_reason':'end_turn','content':[{'type':'text','text':'{"text":"test"}'}]}))
        self.assertEqual('test',r['output']['text'])
    def test_truncation_and_non_object_rejected(self):
        for reason,text in [('max_tokens','{}'),('end_turn','[]')]:
            with self.assertRaises(ValueError): parse_response(json.dumps({'stop_reason':reason,'content':[{'type':'text','text':text}]}))
    def test_reserves_before_request_and_persists(self):
        before=os.getcwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                for _ in range(3): reserve()
                with self.assertRaises(ValueError): reserve()
                self.assertEqual(3,json.loads(Path('.local/claude-requests.json').read_text())['reserved'])
            finally: os.chdir(before)

import json
import os
from unittest import TestCase, mock
from cloud import Cloud, CloudError, encoded, read_input

ENV={'OC_BASE_URL':'https://example.invalid','OC_TENANT':'test','OC_BEARER':'synthetic-only'}

class CloudContractTests(TestCase):
    def test_config_rejects_insecure_and_sql_identifiers(self):
        for change in [{'OC_BASE_URL':'http://example.invalid'},{'OC_BASE_URL':'https://x.invalid/path'},{'OC_NAMESPACE':'x;DROP'},{'OC_DB_USER':'user'}]:
            with mock.patch.dict(os.environ,dict(ENV,**change),clear=True):
                with self.assertRaises(ValueError): Cloud('test')
    def test_existing_schema_never_overwritten(self):
        with mock.patch.dict(os.environ,ENV,clear=True):
            db=Cloud('test'); db.call=mock.Mock(return_value=b'namespace="other"\ntable="runs_v1"\nprimary_key=["id"]\ncolumns=[]')
            with self.assertRaises(ValueError): db.init()
            self.assertEqual(1,db.call.call_count)
    def test_flat_row_and_payload_roundtrip(self):
        with mock.patch.dict(os.environ,ENV,clear=True):
            db=Cloud('test'); db.call=mock.Mock(return_value=b'{}')
            rid=db.save({'input':'test'},{'passed':True})
            args=db.call.call_args.args; row=json.loads(args[2]); self.assertEqual(rid,row['id']); self.assertNotIn('row',row)
            db.call=mock.Mock(return_value=encoded(row)); self.assertEqual({'passed':True},db.get(rid))
    def test_errors_do_not_leak_body(self):
        self.assertNotIn('synthetic-only',str(CloudError(401)))

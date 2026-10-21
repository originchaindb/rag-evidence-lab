"""Small explicit HTTPS adapter. No fallback database, retries, or secret logging."""
import hashlib
import json
import os
from pathlib import Path
import re
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
import uuid

LIMIT = 1024 * 1024

def load_env(path='.env'):
    p = Path(path)
    if p.exists():
        for line in p.read_text(encoding='utf-8-sig').splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                key, sep, value = line.partition('=')
                if not sep or not re.fullmatch(r'[A-Z_][A-Z_0-9]*', key):
                    raise ValueError('invalid .env assignment')
                os.environ.setdefault(key, value.strip().strip('"').strip("'"))

def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def read_input(path):
    with open(path, 'rb') as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError('input exceeds 1 MiB')
    def no_constant(_):
        raise ValueError('non-finite JSON number')
    value = json.loads(raw, parse_constant=no_constant)
    if not isinstance(value, dict):
        raise ValueError('input must be an object')
    return value

class CloudError(RuntimeError):
    def __init__(self, status):
        self.status = status
        super().__init__(f'OriginChainDB HTTP {status}; response body omitted')

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None

class Cloud:
    def __init__(self, namespace):
        load_env()
        base = os.environ.get('OC_BASE_URL', '').rstrip('/')
        url = urllib.parse.urlsplit(base)
        if url.scheme != 'https' or not url.hostname or url.path or url.query or url.fragment or url.username or url.password:
            raise ValueError('OC_BASE_URL must be an HTTPS origin')
        tenant = os.environ.get('OC_TENANT', '')
        self.namespace = os.environ.get('OC_NAMESPACE', namespace)
        if not re.fullmatch(r'[A-Za-z0-9_-]+', tenant) or not re.fullmatch(r'[a-z][a-z0-9_]{0,47}', self.namespace):
            raise ValueError('invalid tenant or namespace')
        key = os.environ.get('OC_BEARER', '')
        if not key or any(c.isspace() for c in key):
            raise ValueError('OC_BEARER is required without whitespace')
        self.url = base + '/v1/tenants/' + tenant
        self.table = self.namespace + '.runs_v1'
        self.headers = {'Authorization': 'Bearer ' + key}
        user, dbkey = os.environ.get('OC_DB_USER'), os.environ.get('OC_DB_KEY')
        if bool(user) != bool(dbkey):
            raise ValueError('set both OC_DB_USER and OC_DB_KEY')
        if user:
            self.headers.update({'X-OC-DB-User': user, 'X-OC-DB-Key': dbkey})
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def call(self, method, path, body=None, content_type='application/json'):
        headers = dict(self.headers, **{'Content-Type': content_type})
        if method != 'GET':
            headers['Idempotency-Key'] = uuid.uuid4().hex
        request = urllib.request.Request(self.url + path, body, headers, method=method)
        try:
            with self.opener.open(request, timeout=30) as response:
                if response.headers.get('X-OC-Replication') == 'degraded':
                    raise RuntimeError('degraded replication; reconcile run ID before retry')
                data = response.read(LIMIT + 1)
                if len(data) > LIMIT:
                    raise ValueError('database response exceeds limit')
                return data
        except urllib.error.HTTPError as exc:
            raise CloudError(exc.code) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise RuntimeError('database connection failed; write outcome may be unknown') from None

    def init(self):
        expected = {'namespace': self.namespace, 'table': 'runs_v1', 'primary_key': ['id'], 'columns': [
            {'name':n, 'ty':t, 'required': True} for n,t in [('id','str'),('created_ms','i64'),('input_hash','str'),('payload','str')]]}
        try:
            data = self.call('GET', '/schemas/' + self.table)
        except CloudError as exc:
            if exc.status != 404:
                raise
            manifest = f'namespace = "{self.namespace}"\ntable = "runs_v1"\nprimary_key = ["id"]\n'
            for col in expected['columns']:
                manifest += f'[[columns]]\nname = "{col["name"]}"\nty = "{col["ty"]}"\nrequired = true\n'
            try:
                self.call('POST', '/schemas', manifest.encode(), 'text/plain')
            except CloudError as conflict:
                if conflict.status != 409:
                    raise
            data = self.call('GET', '/schemas/' + self.table)
        actual = tomllib.loads(data.decode())
        columns = lambda s: sorted((c['name'], c['ty'], c.get('required', False)) for c in s['columns'])
        if any(actual.get(k) != expected[k] for k in ('namespace','table','primary_key')) or columns(actual) != columns(expected):
            raise ValueError('incompatible existing schema; use a fresh namespace')

    def save(self, source, report, run_id=None):
        row = {'id':run_id or uuid.uuid4().hex, 'created_ms':time.time_ns()//1000000,
               'input_hash':hashlib.sha256(encoded(source)).hexdigest(), 'payload':encoded(report).decode()}
        self.call('POST', '/rows/' + self.table, encoded(row))
        return row['id']

    def get(self, run_id):
        if not re.fullmatch(r'[a-f0-9]{32}',run_id):
            raise ValueError('invalid run ID')
        row = json.loads(self.call('GET', '/rows/' + self.table + '/' + run_id))
        if row['id'] != run_id:
            raise ValueError('database returned wrong ID')
        return json.loads(row['payload'])

    def list(self):
        sql = f'SELECT id, created_ms, input_hash FROM {self.table} ORDER BY created_ms DESC LIMIT 20'
        rows = json.loads(self.call('POST','/sql',encoded({'sql':sql}))).get('rows')
        if not isinstance(rows,list):
            raise ValueError('invalid SQL response')
        return rows

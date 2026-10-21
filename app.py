"""Offline evaluation is the default; cloud writes require an explicit command."""
import json
import sys
import uuid
from cloud import Cloud, encoded, read_input
from logic import evaluate

NAMESPACE = 'rag_evidence_lab'

def main(argv):
    if len(argv) < 2 or argv[1] not in ('run','save','cloud-smoke','get','list','gate'):
        raise ValueError('usage: python app.py run|gate|save|cloud-smoke INPUT.json | get RUN_ID | list')
    command = argv[1]
    if command in ('run','gate','save','cloud-smoke'):
        if len(argv) != 3:
            raise ValueError('one input file is required')
        source = read_input(argv[2])
        result = evaluate(source)
        if command in ('run','gate'):
            print(json.dumps(result,indent=2,allow_nan=False))
            return 2 if command=='gate' and not result.get('passed',False) else 0
        db = Cloud(NAMESPACE)
        db.init()
        run_id = uuid.uuid4().hex
        print('Saving run ID: ' + run_id, file=sys.stderr)
        db.save(source,result,run_id)
        if command == 'cloud-smoke':
            fresh = Cloud(NAMESPACE)
            fresh.init()
            if encoded(fresh.get(run_id)) != encoded(result) or not any(r['id']==run_id for r in fresh.list()):
                raise ValueError('cloud round-trip mismatch')
        print(json.dumps({'run_id':run_id,'cloud_verified':command=='cloud-smoke'}))
    elif command == 'get':
        if len(argv)!=3:
            raise ValueError('one run ID is required')
        print(json.dumps(Cloud(NAMESPACE).get(argv[2]),indent=2))
    else:
        if len(argv)!=2:
            raise ValueError('list takes no arguments')
        print(json.dumps(Cloud(NAMESPACE).list(),indent=2))
    return 0

if __name__=='__main__':
    try:
        sys.exit(main(sys.argv))
    except (ValueError,KeyError,TypeError,RuntimeError,OSError) as exc:
        # Never echo input data or provider bodies into diagnostics.
        print('Error: operation failed ('+type(exc).__name__+'). Check input contract and private configuration.',file=sys.stderr)
        sys.exit(1)

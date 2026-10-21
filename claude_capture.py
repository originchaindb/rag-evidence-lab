"""Optional, explicit one-request capture. No tool use, retries or cloud writes."""
import json
import os
from pathlib import Path
import sys
import urllib.request
from cloud import NoRedirect, encoded, load_env, read_input

def parse_response(raw):
    value=json.loads(raw)
    if value.get('stop_reason')!='end_turn':
        raise ValueError('incomplete or refused response')
    blocks=value.get('content')
    if not isinstance(blocks,list) or len(blocks)!=1 or blocks[0].get('type')!='text':
        raise ValueError('expected one text block')
    result=json.loads(blocks[0]['text'])
    if not isinstance(result,dict):
        raise ValueError('expected JSON object')
    return {'output':result,'usage':value.get('usage',{}),'model':value.get('model')}

def reserve():
    directory=Path('.local');directory.mkdir(exist_ok=True)
    lock=directory/'claude.lock'
    # An interrupted request consumes its reservation; a stale lock needs review.
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        path=directory/'claude-requests.json'
        count=json.loads(path.read_text())['reserved'] if path.exists() else 0
        if type(count) is not int or count<0 or count>=3:
            raise ValueError('local three-request allowance exhausted')
        tmp=directory/'claude-requests.tmp';tmp.write_text(json.dumps({'reserved':count+1}))
        tmp.replace(path)
    finally:
        os.close(fd);lock.unlink()

def capture(request):
    load_env()
    model,key=os.environ.get('AI_MODEL'),os.environ.get('ANTHROPIC_API_KEY')
    if not model or not key: raise ValueError('AI_MODEL and ANTHROPIC_API_KEY required')
    if set(request)!={'system','prompt','schema'} or not isinstance(request['system'],str) or not isinstance(request['prompt'],str) or not isinstance(request['schema'],dict):
        raise ValueError('invalid capture request')
    body=encoded({'model':model,'max_tokens':1000,'system':request['system'],
        'messages':[{'role':'user','content':request['prompt']}],
        'output_config':{'format':{'type':'json_schema','schema':request['schema']}}})
    if len(body)>12000: raise ValueError('request exceeds 12000 bytes')
    reserve()
    req=urllib.request.Request('https://api.anthropic.com/v1/messages',data=body,
        headers={'x-api-key':key,'anthropic-version':'2023-06-01','Content-Type':'application/json'},method='POST')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(req,timeout=45) as response:
        raw=response.read(1024*1024+1)
    if len(raw)>1024*1024: raise ValueError('response exceeds limit')
    return parse_response(raw)

if __name__=='__main__':
    try:
        if len(sys.argv)!=3 or sys.argv[1]!='--live':
            raise ValueError('usage: python claude_capture.py --live examples/model-request.json')
        result=capture(read_input(sys.argv[2]))
        path=Path('.local/claude-output.json');path.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print('Saved .local/claude-output.json. Review and merge output into the evaluation fixture; no action executed.')
    except Exception:
        print('Claude capture failed. Check private configuration, request allowance and API access. No automatic retry.',file=sys.stderr)
        sys.exit(1)

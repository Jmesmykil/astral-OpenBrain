"""Read-only compatibility check before a hub deploy; never starts services or prints keys."""
import base64, hashlib, json, sys, urllib.request
from pathlib import Path

def verify(root, expected, get=None):
    root=Path(root)
    node=root/'openhome_devkit/openhome-node-server'
    app=root/'openhome_devkit/openhome-dashboard-pi'
    checks=[(node/'astral_turn_router.cjs',expected['bridge_sha256']),
            (node/'astral_capability.cjs',expected['native_dispatch_sha256']),
            (app/'src/App.tsx',expected['app_sha256'])]
    for path,digest in checks:
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise RuntimeError('Paired browser installation does not match this release: '+path.name)
    if get is None:
        def get(url, authenticated=False):
            headers={}
            if authenticated:
                token=(root/'astral-voice/state/turn-router/token').read_text().strip()
                headers['Authorization']='Bearer '+token
            request=urllib.request.Request(url,headers=headers)
            with urllib.request.urlopen(request,timeout=4) as response:return response.read()
    status=json.loads(get('http://127.0.0.1:3031/status',True))
    if not status.get('ok') or not status.get('connected'):
        raise RuntimeError('The paired browser is not registered with the turn router')
    for relative,digest in expected['assets'].items():
        url='http://127.0.0.1:3000/'+relative.removeprefix('dist/')
        if hashlib.sha256(get(url,False)).hexdigest()!=digest:
            raise RuntimeError('Served browser asset does not match this release: '+relative)
    return {'ok':True,'paired_browser':True,'checked_assets':len(expected['assets'])}

if __name__=='__main__':
    try:
        expected=json.loads(base64.b64decode(sys.argv[1]))
        print(json.dumps(verify(Path.home(),expected)))
    except Exception as error:
        print('Turn-router preflight failed: '+str(error),file=sys.stderr)
        sys.exit(1)

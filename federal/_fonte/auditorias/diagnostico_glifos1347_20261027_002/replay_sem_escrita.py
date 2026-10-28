"""Reconstrói o diagnóstico dos mesmos insumos, sem escrita, rede ou HEAD novo."""
from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;source=(B/'diagnosticar.py').read_text();receipt=json.loads((B/'recibo_replay.json').read_bytes());sha=lambda x:hashlib.sha256(x).hexdigest();assert sha(source.encode())==receipt['sha256_analisador'];assert sha((B/'diagnostico1347.json').read_bytes())==receipt['sha256_resultado'];ns={'__file__':str(B/'diagnosticar.py'),'__name__':'replay_estatico_sem_escrita'};exec(compile(source[:source.index('lexical=[]')],'loader_predicado_congelados','exec'),ns);expected=json.loads((B/'diagnostico1347.json').read_bytes());by={r['path']:r for r in expected['registros']};assert len(ns['docs'])==len(by)==1347
for doc in ns['docs']:
 got=json.loads(json.dumps(ns['analyze'](doc)));old={k:v for k,v in by[doc['path']].items() if k!='HEAD_atual'};assert got==old,doc['path']
assert ns['tinycss2'].__version__==expected['motores']['tinycss2'] and ns['cssselect2'].__version__==expected['motores']['cssselect2'] and ns['html5lib'].__version__==expected['motores']['html5lib'];print('Replay estático idêntico em 1.347 fontes: CSS/glifos/escopos, sem escrita ou rede.')

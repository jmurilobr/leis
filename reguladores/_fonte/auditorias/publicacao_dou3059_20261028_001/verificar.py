"""Verifica o envelope congelado sem escrita ou operações Git."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[4];B=Path(__file__).resolve().parent
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
 return h.hexdigest()
def verificar():
 e=json.loads((B/'envelope.json').read_text())
 for p,s in e['arquivos'].items():
  assert not Path(p).is_absolute() and '..' not in Path(p).parts,p
  assert sha(R/p)==s,p
 parts=[json.loads((B/f'parte{i:03}-normas.json').read_text()) for i in (1,2)]
 assert list(map(len,parts))==[1500,1559]
 assert not set(parts[0])&set(parts[1])
 allnorm={**parts[0],**parts[1]}
 assert len(allnorm)==3059
 assert not any('804-de-10-de-abril-de-2017-20162170.md' in p for p in allnorm)
 actual={p:s for p,s in e['arquivos'].items() if p.startswith('reguladores/') and '/_fonte/' not in p and p.endswith('.md')}
 assert actual==allnorm
 stage=(B/'stage-final.paths.z').read_bytes().split(b'\0');assert stage[-1]==b''
 paths={p.decode() for p in stage[:-1]}
 assert paths==set(e['arquivos'])|{str(B.relative_to(R)/'envelope.json'),str(B.relative_to(R)/'stage-final.paths.z')}
 for c in e['copias_ROOT']:
  assert sha(R/c['origem'])==c['sha256']==sha(R/c['destino'])
 print(json.dumps({'normas':len(allnorm),'arquivos_SHA':len(e['arquivos']),'stage_paths':len(paths),'partes':[1500,1559],'canonicos_extras':0,'divergencias':0}))
if __name__=='__main__':verificar()

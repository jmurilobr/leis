"""Verificador portátil: origens privadas são identificadores históricos, nunca dependências."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[4]
B=R/'reguladores/_fonte/auditorias/publicacao_dou3059_20261028_001'
PIN='4c9190cad18ac7e2e907f4b1d5b8d23ff344f738dfee01010c12485d4ec9ac9e'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
 return h.hexdigest()
def main():
 assert sha(B/'envelope.json')==PIN
 e=json.loads((B/'envelope.json').read_text())
 for p,s in e['arquivos'].items():
  assert not Path(p).is_absolute() and '..' not in Path(p).parts,p
  assert not p.startswith(('_fonte/','municipais/')),p
  assert sha(R/p)==s,p
 copies=json.loads((B/'cobertura-copias.json').read_text())['copias_identicas']
 assert copies==e['copias_ROOT'] and len(copies)==5
 assert len({c['origem'] for c in copies})==len({c['destino'] for c in copies})==5
 for c in copies:
  assert c['origem'].startswith('_fonte/operacao_root_20261027/')
  assert c['destino'].startswith(str(B.relative_to(R))+'/cobertura-ROOT/')
  assert e['arquivos'][c['destino']]==c['sha256']==sha(R/c['destino'])
  assert (R/c['destino']).stat().st_size==c['bytes']
 parts=[json.loads((B/f'parte{i:03}-normas.json').read_text()) for i in (1,2)]
 assert list(map(len,parts))==[1500,1559] and not set(parts[0])&set(parts[1])
 norms={**parts[0],**parts[1]}
 actual={p:s for p,s in e['arquivos'].items() if p.startswith('reguladores/') and '/_fonte/' not in p and p.endswith('.md')}
 assert actual==norms and len(norms)==3059
 assert not any('804-de-10-de-abril-de-2017-20162170.md' in p for p in norms)
 stage=(B/'stage-final.paths.z').read_bytes().split(b'\0');assert stage[-1]==b''
 assert {p.decode() for p in stage[:-1]}==set(e['arquivos'])|{str(B.relative_to(R)/'envelope.json'),str(B.relative_to(R)/'stage-final.paths.z')}
 print(json.dumps({'normas':3059,'partes':[1500,1559],'SHA_verificados':len(e['arquivos']),'copias_ROOT_verificadas':5,'origens_privadas_abertas':0,'normas_municipais_abertas':0,'problemas':0}))
if __name__=='__main__':main()

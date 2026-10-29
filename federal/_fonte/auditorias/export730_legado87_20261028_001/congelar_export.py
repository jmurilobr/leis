"""Mapa efetivo usa arquivos versionados; originais são apenas antecedente."""
from pathlib import Path
import json,hashlib
E=Path(__file__).resolve().parent;R=E.parents[3];O=E.with_name('promocao730_20261028_001');A=E.with_name('alimentacao_normas_20261028_019');sha=lambda b:hashlib.sha256(b).hexdigest();versions=json.loads((E/'mapa_versoes.json').read_bytes());logical={};effective={}
def claim(path,digest):
 if path in logical:assert logical[path]==digest,path
 logical[path]=digest
 row=versions['versoes_logicas'].get(path);actual=row['path_exportado']if row else path
 if path.startswith('scripts/'):assert row,'Global lógico sem export explícito'
 assert sha((R/actual).read_bytes())==digest,(path,actual)
 if actual in effective:assert effective[actual]==digest
 effective[actual]=digest
for hp in [A/'pacote_final001/entrega-hashes.json',A/'entrega-replay-portavel-hashes.json',O/'entrega-hashes.json']:
 rec=json.loads(hp.read_bytes());claim(str(hp.relative_to(R)),sha(hp.read_bytes()))
 for row in rec['arquivos']:claim(row['path'],row['sha256'])
 lp=hp.parent/('entrega-replay-portavel-paths.txt'if hp.parent==A else'entrega-paths.txt');assert sha(lp.read_bytes())==rec['sha256_lista'];claim(str(lp.relative_to(R)),sha(lp.read_bytes()))
for row in json.loads((O/'recibo730.json').read_bytes())['codigos']:claim(row['path'],row['sha256'])
for row in json.loads((O/'recibo_promocao730.json').read_bytes())['insumos']:claim(row['path'],row['sha256'])
assert 'scripts/html2md.py'in logical and 'scripts/baixar_federal.py'in logical
for p in E.rglob('*'):
 if p.is_file()and'__pycache__'not in p.parts and p.name not in {'mapa_logico_antecedente730.json','mapa_efetivo730.json','entrega-paths.txt','entrega-hashes.json'}:effective[str(p.relative_to(R))]=sha(p.read_bytes())
(E/'mapa_logico_antecedente730.json').write_text(json.dumps(dict(sorted(logical.items())),ensure_ascii=False,indent=2)+'\n');effective[str((E/'mapa_logico_antecedente730.json').relative_to(R))]=sha((E/'mapa_logico_antecedente730.json').read_bytes());assert not any(p.startswith('scripts/')for p in effective);assert 'scripts/html2md.py'not in effective and'scripts/baixar_federal.py'not in effective;(E/'mapa_efetivo730.json').write_text(json.dumps(dict(sorted(effective.items())),ensure_ascii=False,indent=2)+'\n');files=[R/p for p in effective]+[E/'mapa_efetivo730.json'];lp=E/'entrega-paths.txt';lp.write_text(''.join(str(p.relative_to(R))+'\n'for p in files));(E/'entrega-hashes.json').write_text(json.dumps({'sha256_lista':sha(lp.read_bytes()),'sha256_mapa_efetivo':sha((E/'mapa_efetivo730.json').read_bytes()),'escritas_canonicas':0,'globals_excluidos':['scripts/html2md.py','scripts/baixar_federal.py'],'arquivos':[{'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes())}for p in files]},ensure_ascii=False,indent=2)+'\n');print('Mapa efetivo',len(effective),'arquivos antes de aplicação; SHA',sha((E/'mapa_efetivo730.json').read_bytes()),flush=True)

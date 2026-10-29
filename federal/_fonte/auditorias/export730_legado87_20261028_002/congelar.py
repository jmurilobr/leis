from pathlib import Path
import json,hashlib
E=Path(__file__).resolve().parent;R=E.parents[3];A=E.with_name('export730_legado87_20261028_001');sha=lambda b:hashlib.sha256(b).hexdigest();mapping=json.loads((A/'mapa_efetivo730.json').read_bytes())
for path,digest in mapping.items():assert sha((R/path).read_bytes())==digest,path
for name in ['mapa_efetivo730.json','entrega-paths.txt','entrega-hashes.json']:mapping[str((A/name).relative_to(R))]=sha((A/name).read_bytes())
for p in E.rglob('*'):
 if p.is_file()and'__pycache__'not in p.parts and p.name not in {'mapa_efetivo730.json','entrega-paths.txt','entrega-hashes.json'}:mapping[str(p.relative_to(R))]=sha(p.read_bytes())
assert not any(p.startswith('scripts/')for p in mapping);assert 'scripts/html2md.py'not in mapping and'scripts/baixar_federal.py'not in mapping;mp=E/'mapa_efetivo730.json';assert not mp.exists();mp.write_text(json.dumps(dict(sorted(mapping.items())),ensure_ascii=False,indent=2)+'\n');files=[R/p for p in mapping]+[mp];lp=E/'entrega-paths.txt';lp.write_text(''.join(str(p.relative_to(R))+'\n'for p in files));(E/'entrega-hashes.json').write_text(json.dumps({'sha256_lista':sha(lp.read_bytes()),'sha256_mapa_efetivo':sha(mp.read_bytes()),'globals_nao_incluidos':['scripts/html2md.py','scripts/baixar_federal.py'],'canônicos_criados_pelo_agente':0,'arquivos':[{'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes())}for p in files]},ensure_ascii=False,indent=2)+'\n');print(len(files),'paths; mapa',sha(mp.read_bytes()),'recibo',sha((E/'recibo_exportacao.json').read_bytes()),flush=True)

"""Recibos imutáveis de candidatos preexistentes e artefatos de qualificação."""
from pathlib import Path
import json,hashlib,collections
B=Path(__file__).resolve().parent;R=B.parents[3];D=B/'pacote3060_001';sha=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((D/'manifesto3060.json').read_bytes());assert len(m['documentos'])==3060;assert '"selecionados_reproduzidos": 3060'in(D/'replay_v4.log').read_text();assert '"selecionados_ineditos_path_identidade_URL_e_transversal": 3060'in(D/'HEAD.log').read_text();codes={R/p:digest for p,digest in m['codigo'].items()};files=[]
for p in B.iterdir():
 if p.is_file()and p.name not in {'entrega-paths.txt','entrega-hashes.json'}:files.append(p)
files.extend(p for p in D.iterdir()if p.is_file());files.extend(codes)
# The qualification used this unchanged antecedent risk predicate; replay v4 uses the frozen CSS module.
p=R/'scripts/auditar_dou_css_tabelas_privado_20261027.py';files.append(p)
for p in codes:assert sha(p.read_bytes())==codes[p]
for r in m['documentos']:
 p=R/r['path'];assert sha(p.read_bytes())==r['sha256_md'];files.append(p)
files=list(dict.fromkeys(files));mapping={str(p.relative_to(R)):sha(p.read_bytes())for p in files};mp=B/'mapa_flat3060.json';assert not mp.exists();mp.write_text(json.dumps(dict(sorted(mapping.items())),ensure_ascii=False,indent=2)+'\n');files.append(mp);artifact=[p for p in files if not str(p.relative_to(R))in{r['path']for r in m['documentos']}];(B/'entrega-MD-preexistentes-paths.txt').write_text(''.join(r['path']+'\n'for r in m['documentos']));(B/'entrega-artefatos-paths.txt').write_text(''.join(str(p.relative_to(R))+'\n'for p in artifact));lp=B/'entrega-paths.txt';lp.write_text(''.join(str(p.relative_to(R))+'\n'for p in files));(B/'entrega-hashes.json').write_text(json.dumps({'sha256_lista':sha(lp.read_bytes()),'MD_preexistentes':3060,'artefatos_ou_dependencias':len(artifact),'arquivos':[{'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes())}for p in files]},ensure_ascii=False,indent=2)+'\n');print('Arquivos',len(files),'MD preexistentes',3060,'manifesto',sha((D/'manifesto3060.json').read_bytes()),'mapa',sha(mp.read_bytes()),flush=True)

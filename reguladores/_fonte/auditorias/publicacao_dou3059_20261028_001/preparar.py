"""Mapa de publicação por seleção explícita; não executa Git nem altera atos."""
from pathlib import Path
import hashlib,json,datetime
R=Path(__file__).resolve().parents[4]
B=Path(__file__).resolve().parent
S=R/'reguladores/_fonte/auditorias/dou2017_selecao3059_20261028_001'
C=R/'reguladores/_fonte/auditorias/chamada_compacta_portavel_20261028_001'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for v in iter(lambda:f.read(1024*1024),b''):h.update(v)
 return h.hexdigest()
def write(name,obj):
 p=B/name
 with p.open('x',encoding='utf8') as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def rel(p):return p.relative_to(R).as_posix()
def merge(dst,p,sha):
 if p in dst and dst[p]!=sha:raise ValueError(('SHA divergente',p))
 assert digest(R/p)==sha,p
 dst[p]=sha
expected={'manifesto3059.json':'8ad9db14bdbca9c2a631732e2523a10dbfe6c3dd223a165e971b618f56cc92fe','entrega-paths.txt':'4cfda9f46c3a2992ac053aa5495677eff3e3d18580ef9ebd8788ec75f0cb310a','mapa_flat3059.json':'cd4ee9df4d298bb1208c9b5c81530247f4d132ec3b46e9e0b508f291069cab27'}
for n,s in expected.items():assert digest(S/n)==s,n
manifest=json.loads((S/'manifesto3059.json').read_text())
normas={x['path']:x['sha256_md'] for x in manifest['documentos']}
assert len(normas)==3059
retido='reguladores/mapa/portarias/2017/portaria-n-804-de-10-de-abril-de-2017-20162170.md'
assert retido not in normas
m={}
for directory,count in [(S,3149),(C,37)]:
 a=json.loads((directory/'entrega-hashes.json').read_text())['arquivos']
 assert len(a)==count
 for x in a:merge(m,x['path'],x['sha256'])
 for name in ['entrega-paths.txt','entrega-hashes.json']:
  merge(m,rel(directory/name),digest(directory/name))
assert digest(C/'manifesto8000.json')=='18e6142f39f3df44aecc8fd5f05c0e76a85b69e88a75d1c050b4ac12d162730d'
def canonical(p):return p.startswith('reguladores/') and '/_fonte/' not in p and p.endswith('.md')
assert {p:m[p] for p in m if canonical(p)}==normas
root=R/'_fonte/operacao_root_20261027'
inputs=[root/'cobertura-continuacao-DOU-ROOT'/n for n in ['recibo.json','federal-blobs.jsonl.gz','reguladores-blobs.jsonl.gz']]+[root/'conferir-cobertura-continuacao-DOU.py',root/'cobertura-continuacao-DOU-root.log']
D=B/'cobertura-ROOT';D.mkdir()
copies=[]
for src in inputs:
 dst=D/src.name
 with src.open('rb') as f,dst.open('xb') as g:
  for chunk in iter(lambda:f.read(1024*1024),b''):g.write(chunk)
 sha=digest(src);assert digest(dst)==sha
 copies.append({'origem':rel(src),'destino':rel(dst),'sha256':sha,'bytes':src.stat().st_size})
 merge(m,rel(dst),sha)
write('cobertura-copias.json',{'copias_identicas':copies,'limite':'Prova de leitura e reconciliação de metadados/OID; não é auditoria substantiva universal nem certificação de vigência. Os caminhos lógicos originais permanecem nos recibos históricos. Cópias propostas para publicação, sem mudança dos originais.'})
control={p:s for p,s in m.items() if p not in normas}
ordered=sorted(normas)
for i,paths in enumerate([ordered[:1500],ordered[1500:]],1):
 subset={p:normas[p] for p in paths}
 write(f'parte{i:03}-normas.json',subset)
 (B/f'parte{i:03}-normas.paths.txt').write_text('\n'.join(paths)+'\n')
 (B/f'parte{i:03}-normas.paths.z').write_bytes(b'\0'.join(p.encode() for p in paths)+b'\0')
write('controles-originais.json',control)
# Adicionais do overlay são incluídos explicitamente; manifesto final não referencia a si próprio.
for p in sorted(B.rglob('*')):
 if p.is_file():merge(m,rel(p),digest(p))
write('mapa-publicacao.json',dict(sorted(m.items())))
merge(m,rel(B/'mapa-publicacao.json'),digest(B/'mapa-publicacao.json'))
(B/'publicacao.paths.txt').write_text('\n'.join(sorted(m))+'\n')
(B/'publicacao.paths.z').write_bytes(b'\0'.join(p.encode() for p in sorted(m))+b'\0')
controls=sorted(set(m)-set(normas))
(B/'controles.paths.z').write_bytes(b'\0'.join(p.encode() for p in controls)+b'\0')
write('manifesto-publicacao.json',{'captura_controle':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).isoformat(),'normas':3059,'partes':[1500,1559],'arquivos_mapa':len(m),'bytes_mapa':sum((R/p).stat().st_size for p in m),'mapa':rel(B/'mapa-publicacao.json'),'sha256_mapa':digest(B/'mapa-publicacao.json'),'sha256_lista':digest(B/'publicacao.paths.txt'),'sha256_nul':digest(B/'publicacao.paths.z'),'sha256_controles_nul':digest(B/'controles.paths.z'),'retido_excluido':retido,'canonicos_extras':0,'divergencias_SHA':0,'copias_ROOT':copies,'limites':'Seleção exclusiva dos 3059 documentos do manifesto final. Antecedentes 3060 e prova de 8000 são somente controles, sem inclusão dos respectivos corpora. Não aplica, não modifica atos e não escreve Git. Baseline histórico ROOT457a preservado; alterações posteriores exigem delta por OID.'})
print(json.dumps({'normas':len(normas),'arquivos':len(m),'manifesto':rel(B/'manifesto-publicacao.json'),'sha256':digest(B/'manifesto-publicacao.json')},ensure_ascii=False))

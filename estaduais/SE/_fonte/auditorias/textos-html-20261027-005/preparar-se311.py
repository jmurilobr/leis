"""Congela candidatos sem tocar canônicos; executado uma vez após QA contextual."""
import json,gzip,hashlib,re,datetime,shutil
from pathlib import Path
SHA=lambda b:hashlib.sha256(b).hexdigest()
base=Path('estaduais/SE/_fonte/auditorias/textos-html-20261027-005')
out=Path('estaduais/SE/_fonte/auditorias/se311-privado-20261027-003');out.mkdir(exist_ok=False)
snapshot=Path('scripts/estados/snapshots/se_html_recente_20261027_003');snapshot.mkdir(exist_ok=False)
old=Path('scripts/estados/snapshots/se_html_recente_20261027_002')
for p in old.glob('*.py'):
 src=Path('scripts/estados')/p.name
 if not src.exists():src=Path('scripts')/p.name
 shutil.copy2(src,snapshot/p.name)
for name in ['visuais_word_spl.py','test_visuais_word_spl.py']:
 shutil.copy2(Path('scripts/estados')/name,snapshot/name)
code={str(p):SHA(p.read_bytes()) for p in snapshot.glob('*.py')}
head=json.load(open(base/'HEAD-atual-controle.json'))
records=[json.loads(ln) for ln in gzip.open(head['arquivo'],'rt')]
assert len(records)==head['total']==10099 and SHA(Path(head['arquivo']).read_bytes())==head['sha256']
byid={};bykey={};byurl={};paths_HEAD={r['path'] for r in records}
for r in records:
 m=r['meta'];u=m.get('fonte','');id=re.search(r'aleselegis[.]al[.]se[.]leg[.]br/legislacao/norma.aspx\?id=(\d+)\b',u)
 if id:byid.setdefault(id[1],[]).append(r['path'])
 if m.get('numero') and m.get('data'):bykey.setdefault((r['path'].split('/')[2],str(m['numero']).replace('.','').upper(),str(m['data'])[:4]),[]).append(r['path'])
 if m.get('arquivo'):byurl.setdefault(m['arquivo'].replace('http://','https://'),[]).append(r['path'])
q=json.load(open(base/'QA-final-v3.json'));passed=q['passaram'];assert len(passed)==311
contexts=json.load(open(base/'contextos-anexos-final-v2.json'));byctx={r['id']:r for r in contexts['contextos_anexos']}
images=json.load(open('scripts/estados/manifestos/se-visuais-html-20261027-005.json'))['capturas']
ids={r['captura']['item']['id'] for r in passed};images=[r for r in images if r['id'] in ids]
assert len(images)==311
rows=[];seen=set();dependencies=set(code)
for r in passed:
 c=r['captura'];it=c['item'];folder='leis-complementares' if it['tipo']=='Lei Complementar' else 'leis-ordinarias';key=(folder,it['numero'],str(it['ano']));prefix='c' if folder=='leis-complementares' else 'l';path=f"estaduais/SE/{folder}/{it['ano']}/{prefix}-{it['numero']}-{it['ano']}-id{it['id']}.md"
 assert it['id'] not in byid and key not in bykey and c['url'].replace('http://','https://') not in byurl and path not in paths_HEAD
 assert key not in seen;seen.add(key)
 if it['id'] in byctx:assert byctx[it['id']]['decisao']!='reter'
 title=f"{it['tipo']} nº {it['numero']}, de {it['data']}"
 text=r['body'];publication='; '.join(dict.fromkeys(p['trecho'] for p in r['QA']['rodapes_publicacao'])) or None
 meta=dict(titulo=title,uf='SE',tipo=it['tipo'],numero=it['numero'],data=it['data'],ementa=it['ementa'],situacao=it['situacao'],revogada=None,versao_texto='HTML integral fornecido pela ALESE; edição histórica/compilação não declarada; igualdade à edição DOE não certificada',publicacao=publication,fonte=it['fonte'],arquivo=c['url'],baixado_em=c['capturado_em'][:10])
 md=('---\n'+''.join(k+': '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in meta.items())+'---\n# '+title+'\n\n'+text).encode()
 private=out/'candidatos'/path;private.parent.mkdir(parents=True,exist_ok=True);private.write_bytes(md)
 row=dict(path=path,privado=str(private),sha256_md=SHA(md),captura=c,QA=r['QA'],dedup=dict(HEAD=head['HEAD'],id_ALESE=it['id'],identidade=list(key),arquivo=c['url'],colisoes=[]))
 if it['id'] in byctx:row['contexto_anexo']=byctx[it['id']]['avaliacao']
 rows.append(row);dependencies.update([str(private),c['cache'],it['indice']['cache']])
for r in images:dependencies.add(r['arquivo'])
# A prova visual preserva todos os oito novos brasões revistos, inclusive os não usados pelo lote.
for p in [Path('estaduais/SE/_fonte/auditorias/visuais-html-20261027-005/contato-novos.png'),Path('estaduais/SE/_fonte/auditorias/visuais-html-20261027-005/inventario-novos.json')]:dependencies.add(str(p))
for previous in ['scripts/estados/manifestos/se13-proposta-privada-20261027-001.json','scripts/estados/manifestos/se131-proposta-privada-20261027-003.json']:
 p=json.load(open(previous));assert not ids & {r['captura']['item']['id'] for r in p['documentos']};dependencies.add(previous)
pre=json.load(open(base/'pre-visual.json'));held={r['captura']['item']['id']:dict(captura=r['captura'],erro=r['erro']) for r in pre['retidos']}
for r in q['retidos']:held[r['captura']['item']['id']]=r
allrows=json.load(open('scripts/estados/manifestos/se-textos-html-20261027-005.json'))['capturas']
for r in allrows:
 id=r['item']['id']
 if id not in ids and id not in held:held[id]=dict(captura=r,erro='Imagem de origem externa ao portal; revisão independente necessária, não capturada pelo cliente SE.')
assert len(held)==45 and len(allrows)==len(rows)+len(held)==356
for h in held.values():dependencies.update([h['captura']['cache'],h['captura']['item']['indice']['cache']])
dependencies.update([str(base/'contextos-anexos-final-v2.json'),str(base/'HEAD-atual-controle.json'),head['arquivo'],head['ls_tree_NUL'],str(base/'preparar-se311.py')])
manifest=Path('scripts/estados/manifestos/se311-proposta-privada-20261027-003.json')
m=dict(preparado_em=datetime.datetime.now().astimezone().isoformat(),total=311,total_entrada=356,total_retido=45,metas_inalteradas=True,sem_promocao=True,HEAD_triagem=head['HEAD'],inventario_HEAD=head,documentos=rows,retidos=list(held.values()),imagens=images,codigo=code,testes=36,contextos_anexos=str(base/'contextos-anexos-final-v2.json'),limites='Transcrição integral do HTML oficial isolado ALESE, comparação CommonMark literal e células/linhas/spans/sinais; brasões raster exatos e picture VML institucional contextual. Sem certificação de igualdade à edição DOE. Situação literal do índice não implica vigência presumida: revogada null. Não há OCR corretivo ou alteração de número/data. Quatro dúvidas de rodapé, LOA/anexo externo e outros casos de contexto permanecem explicitamente retidos.',comandos=dict(replay=f'PYTHONPATH="$PWD/scripts/bin/qa-20261027/python" /Users/joaodavisn/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 {snapshot}/reexecutar_spl_html_recente.py --manifesto {manifest} --saida CAMINHO_NOVO.jsonl',testes=f'PYTHONPATH="$PWD/scripts/bin/qa-20261027/python:$PWD/{snapshot}" /Users/joaodavisn/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest test_spl_indice_html test_spl_html_recente test_css_contexto_campo test_visuais_word_spl'))
# Não transportar headers de sessão em controles públicos.
def sensitive(x):
 if isinstance(x,dict):
  for k,v in x.items():
   assert k.lower() not in {'set-cookie','cookie','authorization','proxy-authorization'},k
   sensitive(v)
 elif isinstance(x,list):
  for v in x:sensitive(v)
sensitive(m)
manifest.open('x').write(json.dumps(m,ensure_ascii=False,indent=2)+'\n');dependencies.add(str(manifest))
(out/'dependencias-iniciais.json').write_text(json.dumps(sorted(dependencies),ensure_ascii=False,indent=2)+'\n')
print('manifesto',manifest,'SHA',SHA(manifest.read_bytes()),'documentos',len(rows),'retidos',len(held),'dependencias',len(dependencies),'snapshot',snapshot)

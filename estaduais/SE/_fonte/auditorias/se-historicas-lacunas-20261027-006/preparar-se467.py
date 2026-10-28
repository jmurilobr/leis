"""Congelamento privado das leis históricas, após revisão visual e contextual."""
import sys,json,gzip,hashlib,datetime,os
from pathlib import Path
sys.path.insert(0,'scripts/estados/snapshots/se311_promocao_20261027_001')
from promover_se311 import conferir_dedup
SHA=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=Path('estaduais/SE/_fonte/auditorias/se-historicas-lacunas-20261027-006');out=Path('estaduais/SE/_fonte/auditorias/se467-privado-20261027-005');out.mkdir(exist_ok=False)
head=json.load(open(base/'HEAD-publicacao-005/controle.json'));assert SHA(head['arquivo'])==head['sha256'];HEAD=[json.loads(ln) for ln in gzip.open(head['arquivo'],'rt')]
qa=json.load(open(base/'QA-final-005.json'));contextfile=base/'contextos-objetos-final-471-v3.json';contexts=json.load(open(contextfile));byctx={r['id']:r for r in contexts['contextos']};holds_context={id for id,r in byctx.items() if r['decisao'].startswith('reter')};assert len(holds_context)==4
accepted=[r for r in qa['passaram'] if r['captura']['item']['id'] not in holds_context];assert len(accepted)==467 and not qa['retidos']
images=json.load(open('scripts/estados/manifestos/se-visuais-html-20261027-006.json'))['capturas'];images=[r for r in images if r['id'] in {q['captura']['item']['id'] for q in accepted}];assert len(images)==467
rows=[];candidates=[];dependencies=set()
for r in accepted:
 c=r['captura'];it=c['item'];folder='leis-complementares' if it['tipo']=='Lei Complementar' else 'leis-ordinarias';prefix='c' if folder=='leis-complementares' else 'l';path=f"estaduais/SE/{folder}/{it['ano']}/{prefix}-{it['numero']}-{it['ano']}-id{it['id']}.md";assert not os.path.lexists(path)
 title=f"{it['tipo']} nº {it['numero']}, de {it['data']}";body=r['body'];publication='; '.join(dict.fromkeys(p['trecho'] for p in r['QA']['rodapes_publicacao'])) or None
 meta=dict(titulo=title,uf='SE',tipo=it['tipo'],numero=it['numero'],data=it['data'],ementa=it['ementa'],situacao=it['situacao'],revogada=None,versao_texto='HTML integral fornecido pela ALESE; edição histórica/compilação não declarada; igualdade à edição DOE não certificada',publicacao=publication,fonte=it['fonte'],arquivo=c['url'],baixado_em=c['capturado_em'][:10])
 blob=('---\n'+''.join(k+': '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in meta.items())+'---\n# '+title+'\n\n'+body).encode();private=out/'candidatos'/path;private.parent.mkdir(parents=True,exist_ok=True);private.write_bytes(blob)
 q=dict(path=path,privado=str(private),sha256_md=SHA(private),captura=c,QA=r['QA'],dedup=dict(HEAD=head['HEAD'],id_ALESE=it['id'],identidade=[folder,it['numero'],str(it['ano'])],arquivo=c['url'],colisoes=[]))
 if it['id'] in byctx:q['contexto_objeto']=byctx[it['id']]['avaliacao']
 rows.append(q);candidates.append(dict(path=path,meta=meta));dependencies.update([str(private),c['cache'],it['indice']['cache']])
conferir_dedup(HEAD,candidates)
for r in images:dependencies.add(r['arquivo'])
pre=json.load(open(base/'pre-QA-final-567-v3.json'));held={r['captura']['item']['id']:r for r in pre['retidos']}
for r in qa['passaram']:
 id=r['captura']['item']['id']
 if id in holds_context:held[id]=dict(captura=r['captura'],erro=byctx[id]['avaliacao'],classificacao=byctx[id]['decisao'])
assert len(held)==100 and len(held)+len(rows)==567
for r in held.values():dependencies.update([r['captura']['cache'],r['captura']['item']['indice']['cache']])
for p in ['scripts/estados/manifestos/se13-proposta-privada-20261027-001.json','scripts/estados/manifestos/se131-proposta-privada-20261027-003.json','scripts/estados/manifestos/se311-proposta-privada-20261027-003.json']:
 old=json.load(open(p));assert not {r['captura']['item']['id'] for r in rows}&{r['captura']['item']['id'] for r in old['documentos']}
snapshot=Path('scripts/estados/snapshots/se_html_recente_20261027_005');code={str(p):SHA(p) for p in snapshot.glob('*.py')};dependencies.update(code)
for p in [contextfile,base/'contextos-objetos-complementar-471-v2.json',base/'HEAD-publicacao-005/controle.json',Path(head['arquivo']),Path(head['ls_tree_NUL']),base/'preparar-se467.py',Path('scripts/estados/manifestos/se-textos-html-20261027-006.json'),Path('scripts/estados/manifestos/se-visuais-html-20261027-006.json'),Path('scripts/estados/manifestos/se-indices-html-20261027-006.json'),Path('scripts/estados/manifestos/se-visuais-html-20261027-005.json'),Path('estaduais/SE/_fonte/auditorias/visuais-html-20261027-006/prova-brasoes-final.json'),Path('estaduais/SE/_fonte/auditorias/visuais-html-20261027-006/contato-novos-final.png'),Path('estaduais/SE/_fonte/auditorias/visuais-html-20261027-006/inventario-novos-final.json')]:dependencies.add(str(p))
manifest=Path('scripts/estados/manifestos/se467-proposta-privada-20261027-005.json');m=dict(preparado_em=datetime.datetime.now().astimezone().isoformat(),total=467,total_entrada=567,total_retido=100,sem_promocao=True,metas_inalteradas=True,HEAD_triagem=head['HEAD'],inventario_HEAD=head,documentos=rows,retidos=list(held.values()),imagens=images,codigo=code,testes=40,contextos_objetos=str(contextfile),prova_visuais='Todos471 recursos raster associados (211 URLs,12 SHA distintos) emHTTP200; cinco novos brasões examinados visualmente, demais já conferidos. Apenas467 associações dos candidatos admitidos são usadas nesta proposta.',limites='Transcrição integral do HTML oficial isolado ALESE, comparação CommonMark literal, matrizes/células/spans/sinais, CSS aplicado e VML institucional. Edição DOE não certificada. Revogada null conservador, situação literal separada. Quatro casos contextuais retidos: três ausências de anexos/mapa confirmadas no HTML e uma relação entre tabelas indeterminada; demais retenções são conservadoras e não afirmam defeito coletivo.',comando_replay=f'PYTHONPATH="$PWD/scripts/bin/qa-20261027/python" /Users/joaodavisn/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 {snapshot}/reexecutar_spl_html_recente.py --manifesto {manifest} --saida CAMINHO_NOVO.jsonl')
def check(x):
 if isinstance(x,dict):
  for k,v in x.items():assert k.lower() not in ['set-cookie','cookie','authorization','proxy-authorization'];check(v)
 elif isinstance(x,list):
  for v in x:check(v)
check(m);manifest.open('x').write(json.dumps(m,ensure_ascii=False,indent=2)+'\n');dependencies.add(str(manifest));assert all(not Path(p).is_absolute() and '..' not in Path(p).parts for p in dependencies);(out/'dependencias-iniciais.json').open('x').write(json.dumps(sorted(dependencies),ensure_ascii=False,indent=2)+'\n');print(manifest,SHA(manifest),'total',len(rows),'retidos',len(held),'deps',len(dependencies))

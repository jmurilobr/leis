"""Qualificação privada DOU 2017, sem rede ou escrita canônica."""
from pathlib import Path
import sys,json,gzip,hashlib,re,datetime,ast,subprocess,collections
R=Path.cwd();B=Path(__file__).resolve().parent
C=R/'reguladores/_fonte/auditorias/orgao_dedup_2017_20261028_002/codigo';sys.path[:0]=[str(C),str(R/'scripts/bin/qa-20261027/python'),str(R/'scripts/bin/qa-html5-20261027/python')]
from html.parser import HTMLParser
from representacao_html_dou import _CSS_RISCO,_CLASSE_RISCO
from css_glifos_DOU_snapshot import analyze
from gate_orgao import motivos as motivos_orgao,n
from identidade_cross_snapshot import number,ambiguous
import auditar_cache_dou as audit
import gates_snapshot as gates
code_riscos=(R/'scripts/auditar_dou_css_tabelas_privado_20261027.py').read_text();nodes=[x for x in ast.parse(code_riscos).body if isinstance(x,ast.ClassDef) and x.name=='Riscos' or isinstance(x,ast.FunctionDef) and x.name=='riscos'];assert len(nodes)==2;exec(compile(ast.Module(body=nodes,type_ignores=[]),'riscos_antecedentes','exec'))
import pe_fidelidade_visivel as v
from integridade_html_federal import Visivel
from integridade_anexos_decreto import anexo_proprio_ausente
from markdown_it import MarkdownIt
import html5lib
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((R/'scripts/integridade_anexos_decreto.py').read_bytes())=='e7acf0ce9ada5bb7d0e062dd20afd66724fef43109328046ef519a6e8a23abac'
audit.RAIZ=R
D=B/'faixa10000_14000';D.mkdir(exist_ok=False)
helpers=R/'federal/_fonte/auditorias/commonmark8886_20261027_001/replay_commonmark_html5.py';tree=ast.parse(helpers.read_text());names={'tag','visible','ancestor','matrices','alpha','roman','lists'};nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'BLOCK','SKIP'} for t in n.targets)];assert len(nodes)==9;env={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helpers),'exec'),env)
base=json.loads(gzip.decompress((B/'baseline_reguladores_HEAD_reservas.json.gz').read_bytes()));tracked={x['path'] for x in base['documentos']};keys=collections.defaultdict(list);urls=set();oldkeys=set()
for x in base['documentos']:
 m=x['meta'];k=gates.chave(m,x['path']);keys[k].append(x['path']);urls.add(m.get('fonte'));oldkeys.add(audit.identidade(m))
from epigrafe_tokens_html_privado import epigrafe_tokens
original_epigrafe=audit.epigrafe_do_ato
audit.epigrafe_do_ato=lambda source,fragmento,inicio:epigrafe_tokens(source,fragmento,inicio,original_epigrafe)
index=json.loads(gzip.decompress((B/'indice_federal_HEAD_reservas.json.gz').read_bytes()));federal_keys=collections.defaultdict(list)
for x in index['registros']:federal_keys[(x['tipo'],x['numero'],x['data'])].append(x)
federal_urns={x.get('URN_literal') for x in index['registros']+index['reservas'] if x.get('URN_literal')};federal_urls={x.get('fonte_literal') for x in index['registros']+index['reservas'] if x.get('fonte_literal')}
inputs=json.loads((R/'reguladores/_fonte/auditorias/dou2017_federal_20261028_001/candidatos2017.json').read_bytes())[10000:14000];(D/'entrada4000.json').write_text(json.dumps(inputs,ensure_ascii=False,indent=2)+'\n');accepted=[];held=[];proofs=[];intermediate=[];today=datetime.date.today();engine=MarkdownIt('commonmark',{'html':True,'linkify':False,'typographer':False}).enable('table').enable('strikethrough')
for i,p in enumerate(inputs,1):
 try:
  raw=(R/p).read_bytes();row,m=audit.conferir(R/p,oldkeys,urls,today);body=audit.meta_corpo(raw.decode())[1];src=gzip.decompress((R/row['cache']).read_bytes());source=src.decode();fragment=re.search(r'<div[^>]+class="[^\"]*texto-dou[^\"]*".*?</div>\s*(?=<div|</section|</main)',source,re.S)[0];reasons=gates.motivos_identidade(m,p,keys,urls,tracked)+gates.motivos_conteudo(body)+riscos(fragment,source);parsed=Visivel();parsed.feed(fragment);parsed.close()
  if parsed.visual:reasons.append({'motivo':'objeto visual inclusive comentário condicional','objetos':parsed.visual})
  own=anexo_proprio_ausente(body,parsed)
  if own:reasons.append({'motivo':'guard87 suplementar exige contexto','detalhe':own})
  if re.search(r'(?i)(?:symbol|wingdings|webdings|dingbats)',fragment):reasons.append({'motivo':'fonte especial no campo normativo exige contexto'})
  org=m.get('orgao');header=audit.campo_html(source,'orgao-dou-data');plain=re.sub(r'<[^>]+>',' ',fragment);reasons.extend({'motivo':x}for x in motivos_orgao(org,header,plain));levels=[n(x)for x in str(org).split('/')]
  if any(len(levels)>1 and levels[0]==root and levels[1]==unit for root,unit in ambiguous):reasons.append({'motivo':'Vínculo institucional contextual ambíguo; sem inferir órgão corrigido'})
  typ=index['tipos_explicitamente_comparaveis'].get(n(m['tipo']));num=number(m['numero']);key=(typ,num,m['data'])if typ and num else None
  if typ and not num:reasons.append({'motivo':'Tipo federal comparável sem número/sufixo inequívoco; reserva explícita'})
  if not typ and re.search(r'congresso nacional|senado federal|camara dos deputados',n(org)):reasons.append({'motivo':'Série legislativa institucional sem chave federal inequívoca; reserva explícita'})
  matches=federal_keys.get(key,[])if key else[]
  if matches:reasons.append({'motivo':'Identidade federal já pública ou reservada','chave':key,'coincidencias':matches})
  if m.get('urn')in federal_urns or m.get('fonte')in federal_urls:reasons.append({'motivo':'URN/URL federal já pública ou reservada'})
  ep=n(row['epigrafe_html']);primary_type=next((v for pat,v in [(r'^decreto legislativo\b','dlg'),(r'^decreto[ -]lei\b','del'),(r'^decreto\b','dec'),(r'^lei complementar\b','lc'),(r'^lei delegada\b','ldl'),(r'^lei\b','lei'),(r'^medida provisoria\b','mp'),(r'^emenda constitucional de revisao\b','ecr'),(r'^emenda constitucional\b','ec')]if re.search(pat,ep)),None)
  if primary_type and primary_type!=typ:reasons.append({'motivo':'Tipo da epígrafe primária diverge da série comparável do metadado','tipo_fonte':primary_type,'tipo_meta':typ})
  css=analyze({'path':p,'lote':'DOU2017 faixa10000_14000','sha256_candidato':sha(raw),'source_raw':src,'source':source,'source_url':m['fonte'],'normalizacao':None})
  if any(e['escopo']=='normativo'for e in css['eventos_texto_efetivo_DOM'])or css['seletores_nao_resolvidos']or css['regras_condicionais_com_match']or css['pseudo_elementos_com_match']:reasons.append({'motivo':'CSS/glifo/tachado normativo requer contexto','diagnostico':css})
  st0=html5lib.parse(fragment,treebuilder='etree',namespaceHTMLElements=False);paras=[''.join(e.itertext()).strip()for e in st0.iter()if e.tag in {'p','h1','h2','h3','h4','h5','h6'}];arts=[(j,t)for j,t in enumerate(paras)if re.match(r'^Art(?:igo)?\.?\s*(?:1(?:[ºo°.]|\b)|[úu]nico)\b',t,re.I)];prefix='\n'.join(paras[:arts[0][0]])if arts else'\n'.join(paras[:12])
  if not arts:reasons.append({'motivo':'Sem primeiro dispositivo próprio inequívoco; revisão individual','prefixo':prefix})
  if re.search(r'onde se le|leia[ -]se|retificac|retificar|retifica o|retifica a',n(prefix)):reasons.append({'motivo':'Contexto de retificação antes do dispositivo; edição integral exige revisão','prefixo':prefix})
  if reasons:held.append({'path':p,'sha256_md':sha(raw),'sha256_fonte':sha(src),'cache':row['cache'],'motivos':reasons});continue
  render=engine.render(body);h1=re.search(r'<h1\b[^>]*>.*?</h1>',render,re.S);assert h1 and v.texto_visivel_html(h1[0])==' '.join(m['titulo'].split());render=render[:h1.start()]+render[h1.end():];a=v.texto_visivel_html(fragment);b=v.texto_visivel_html(render);norm,changes=v._heading_comprovado(b,body,a);st=html5lib.parse(fragment,treebuilder='etree',namespaceHTMLElements=False);rt=html5lib.parse(render,treebuilder='etree',namespaceHTMLElements=False);a5=env['visible'](st.find('body'));b5=env['visible'](rt.find('body'))
  for c in changes:b5=b5.replace(c['markdown'],c['fonte'],1)
  sm=env['matrices'](st);rm=env['matrices'](rt);sl=env['lists'](st);rl=env['lists'](rt);checks={'texto_pontuacao_CommonMark':a==norm,'numeros_sinais_CommonMark':v.assinatura_numerica(a)==v.assinatura_numerica(norm),'texto_pontuacao_HTML5':a5==b5,'numeros_sinais_HTML5':v.assinatura_numerica(a5)==v.assinatura_numerica(b5),'matrizes_linhas_celulas_spans_HTML5':sm==rm,'listas_type_start_value_HTML5':sl==rl};q={'path':p,'sha256_md':sha(raw),'sha256_fonte':sha(src),'checks':checks,'normalizacoes_heading':changes,'sha256_render_CommonMark':sha(render.encode()),'sha256_matrizes':sha(json.dumps(sm,ensure_ascii=False,sort_keys=True).encode()),'sha256_listas':sha(json.dumps(sl,ensure_ascii=False,sort_keys=True).encode())}
  if not all(checks.values()):
   q['motivo']='Divergência de texto, sinais, estrutura ou lista; não promovido';q['primeira_diferenca']={'fonte':a[:300],'render':norm[:300]};held.append(q);continue
  k=gates.chave(m,p);keys[k].append(p);urls.add(m['fonte']);oldkeys.add(audit.identidade(m));tracked.add(p);record={**row,'meta':m,'QA':q};accepted.append(record);proofs.append({'path':p,'MD_utf8':raw.decode(),'HTML_utf8':source,'sha256_md':sha(raw),'sha256_fonte':sha(src),'QA':q});intermediate.append({'path':p,'markdown':body,'fragmento':fragment,'normalizacoes':changes})
 except Exception as e:held.append({'path':p,'erro':type(e).__name__+': '+str(e)})
 finally:
  if i%100==0:print(json.dumps({'processados':i,'aptos_preliminares':len(accepted),'retidos':len(held)}),flush=True)
# Motor GFM independente em uma chamada local; não é rede ou render GitHub.
code="import {marked} from 'file:///Volumes/ExternalSSD/GitHub/constituicao/reguladores/_fonte/auditorias/orgao_dedup_2017_20261028_002/codigo/marked.esm.mjs';let t='';for await(const x of process.stdin)t+=x;process.stdout.write(JSON.stringify(JSON.parse(t).map(r=>({path:r.path,html:marked.parse(r.markdown,{gfm:true,pedantic:false,breaks:false})}))));"
marked={r['path']:r['html'] for r in json.loads(subprocess.check_output(['node','--input-type=module','-e',code],input=json.dumps(intermediate).encode()))};final=[];finalproof=[]
for r,pr,z in zip(accepted,proofs,intermediate):
 render=marked[r['path']];h1=re.search(r'<h1\b[^>]*>.*?</h1>',render,re.S);assert h1;render=render[:h1.start()]+render[h1.end():];st=html5lib.parse(z['fragmento'],treebuilder='etree',namespaceHTMLElements=False);rt=html5lib.parse(render,treebuilder='etree',namespaceHTMLElements=False);a=env['visible'](st.find('body'));b=env['visible'](rt.find('body'))
 for c in z['normalizacoes']:b=b.replace(c['markdown'],c['fonte'],1)
 check={'texto_pontuacao_GFM_HTML5':a==b,'numeros_sinais_GFM_HTML5':v.assinatura_numerica(a)==v.assinatura_numerica(b),'matrizes_GFM_HTML5':env['matrices'](st)==env['matrices'](rt),'listas_GFM_HTML5':env['lists'](st)==env['lists'](rt)};r['QA']['checks_GFM']=check;r['QA']['sha256_render_GFM']=sha(render.encode());pr['QA']=r['QA']
 if all(check.values()):final.append(r);finalproof.append(pr)
 else:held.append({'path':r['path'],'sha256_md':r['sha256_md'],'sha256_fonte':r['sha256_html'],'motivo':'Divergência no segundo motor GFM','checks':check})
(D/'fontes_integrais.jsonl.gz').write_bytes(gzip.compress(('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in finalproof)+'\n').encode(),mtime=0));result={'HEAD_baseline':base['HEAD'],'guard_sha256':sha((R/'scripts/integridade_anexos_decreto.py').read_bytes()),'baseline_sha256':sha((B/'baseline_reguladores_HEAD_reservas.json.gz').read_bytes()),'entrada':len(inputs),'aptos_preliminares':len(final),'indice_federal_sha256':sha((B/'indice_federal_HEAD_reservas.json.gz').read_bytes()),'retidos':held,'documentos':final,'limites':'Seleção privada de arquivos preservados em ano com erros. Não certifica cobertura anual, vigência ou identidade visual CSS. Replays CommonMark/GFM, pontuação e estrutura HTML5 completos, sem rede ou reescrita canônica. Alertas conservadores ficam retidos para contexto; nenhum deles integra contagem apta.'};assert len(final)+len(held)==len(inputs);(D/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(D/'selecionados-paths.txt').write_text(''.join(r['path']+'\n' for r in final));print('FIM',len(final),'aptos preliminares',len(held),'retidos',flush=True)

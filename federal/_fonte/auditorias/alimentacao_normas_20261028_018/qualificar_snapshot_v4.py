"""QA privado de um snapshot de respostas concluídas; nenhuma rede ou promoção."""
from pathlib import Path
import sys,json,gzip,hashlib,re,datetime,subprocess,argparse
B=Path(__file__).resolve().parent;ROOT=B.parents[3];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'scripts/bin/qa-20261027/python'))
from zoneinfo import ZoneInfo
import baixar_federal as f,auditar
from comum import yaml_str
from integridade_html_federal import Visivel
from integridade_anexos_decreto import anexo_proprio_ausente
from identidade_decreto import extrair_epigrafe_decreto,numero_normalizado
from identidade_decreto_revisao import normal,FECHO,MESES
from auditar_pontuacao_federal import normalizar_marcador_administrativo,contexto_numerico
from estados import pe_fidelidade_visivel as v
from markdown_it import MarkdownIt
def principal_fechos(body):
 """Conservador: não empresta artigos ou fechos de documento incorporado."""
 seen_article=False;closings=[];boundary=None
 date_pattern=r'(?:RIO DE JANEIRO|BRASILIA)[,.;\s]+(?:EM\s*)?(?:DE\s*)?\d{1,2}[º°]?\s*(?:DE\s*)?[A-Z]+\s*[,;]?\s*(?:DE\s*)?[12]\.?\d{3}'
 article_pattern=r'^(?:ARTIGO|ART\.?)\s*[.º°O]*\s*(?:\d+(?:[.º°O]|\b)|UNICO\b)'
 header_pattern=r'^(?:ANEXOS?|REGULAMENTOS?|REGIMENTOS?|CONVENCOES|CONVENCAO|ESTATUTOS?|ACORDOS?|TABELAS?|RELACOES|RELACAO|INSTRUCOES|MODELOS?|RETIFICACAO|RETIFICACOES)\b'
 for block in body.split('\n\n'):
  text=normal(v.texto_visivel_html(re.sub(r'^\s*#{1,6}\s*','',block)))
  line_articles=any(re.match(article_pattern,normal(v.texto_visivel_html(re.sub(r'^\s*#{1,6}\s*','',line)))) for line in block.splitlines())
  if re.match(header_pattern,text):
   boundary={'bloco_literal':block,'cabecalho_normalizado':text,'artigo_principal_visto':seen_article};break
  if line_articles:seen_article=True
  matches=list(re.finditer(date_pattern,text))
  if matches and not seen_article and re.match(r'^(?:RIO DE JANEIRO|BRASILIA)\b',text):
   return [],{'bloco_literal':block,'motivo':'Fecho antes de qualquer artigo próprio; exige revisão específica do comando principal sem artigos, sem emprestar artigos posteriores.'}
  if not seen_article:continue
  for match in matches:
   found=FECHO.match(match[0]);assert found
   closings.append({'literal_normalizado':match[0],'data':datetime.date(int(found['ano'].replace('.','')),MESES[found['mes']],int(found['dia'])).isoformat(),'bloco_literal':block})
 return closings,boundary

sha=lambda b:hashlib.sha256(b).hexdigest();ap=argparse.ArgumentParser();ap.add_argument('--nome',required=True);args=ap.parse_args();assert re.fullmatch(r'[a-z0-9_]+',args.nome);D=B/args.nome;D.mkdir(exist_ok=False);(D/'candidatos').mkdir();snapshot=json.loads((B/'snapshot_codigo.json').read_bytes());assert sha((ROOT/'scripts/integridade_anexos_decreto.py').read_bytes())==snapshot['guard_sha256'];results=[json.loads(p.read_bytes()) for p in sorted((B/'resultados').glob('*.json'))];rows=[];held=[];render=[]
for rr in results:
 r={'path':rr['path'],'coleta':rr}
 try:
  assert rr['estado']=='fonte_capturada_para_QA',rr.get('motivo',rr['estado']);assert rr['tipo_real']=='HTML','PDF exige QA fac-similar';mdraw=gzip.decompress((ROOT/rr['metadados']['arquivo_raw']).read_bytes());assert sha(mdraw)==rr['metadados']['sha256_raw'];meta=json.loads(mdraw);src=gzip.decompress((ROOT/rr['texto']['arquivo_raw']).read_bytes());assert sha(src)==rr['texto']['sha256_raw'];s=src.decode('utf-8');body=f.convert(s);ep=extrair_epigrafe_decreto(body);assert ep and ep['numero']==numero_normalizado(f.numero_oficial(rr['indice'])) and ep['data']==meta['legislationDate'],'Epígrafe própria inconclusiva ou divergente';assert meta['legislationIdentifier']==rr['urn'];r.update(urn=rr['urn'],epigrafe=ep);sp=Visivel();sp.feed(s);assert not sp.visual,'Objeto visual normativo exige revisão';assert not re.search(r'<(?:ol|ul|li)\b',s,re.I),'Lista HTML normativa exige replay estrutural específico';assert not re.search(r'^\s*RETIFICA[ÇC](?:[ÃA]O|[ÕO]ES)\s*$',body[:re.search(r'^\s*(?:\*\*)?Art',body,re.M|re.I).start()] if re.search(r'^\s*(?:\*\*)?Art',body,re.M|re.I) else body,re.M|re.I),'Retificação avulsa ou contexto ambíguo antes dos artigos';partial=f.motivo_texto_parcial_decreto('DEC-n',body);assert not partial,partial;anexo=anexo_proprio_ausente(body,sp);assert not anexo,anexo
  closing,boundary=principal_fechos(body);r['limite_documento_incorporado']=boundary;assert len(closing)==1 and closing[0]['data']==ep['data'],'Fecho do principal ausente, múltiplo ou divergente antes de documento incorporado';r['limite_documento_incorporado']=boundary;norm,admin=normalizar_marcador_administrativo(s,r);d=rr['indice'];cab=['---','titulo: '+yaml_str(d['normaNome'].strip()),'tipo: "Decreto"','numero: '+yaml_str(f.numero_oficial(d)),'data: '+ep['data'],'ementa: '+yaml_str(d['ementa']),'revogada: null','forca_legal_fonte: '+yaml_str(json.dumps(f.como_lista(meta.get('legislationLegalForce')),ensure_ascii=False)),'fonte_metadados: '+yaml_str(f.API_NORMA.format(rr['urn'])),'sha256_metadados_fonte: '+yaml_str(sha(mdraw)),'versao_texto: '+yaml_str('original' if rr['encoding_escolhido']['version']=='Original' else 'compilada (texto vigente)'),'urn: '+yaml_str(rr['urn']),'fonte: '+yaml_str('https://normas.leg.br/?urn='+rr['urn']),'baixado_em: '+datetime.datetime.fromisoformat(rr['texto']['captura_utc']).astimezone(ZoneInfo('America/Recife')).date().isoformat(),'---'];raw=('\n'.join(cab)+'\n# '+d['normaNome'].strip()+'\n\n'+body).encode();assert not (ROOT/r['path']).exists(),'Destino canônico existe';errors,warnings=auditar.validar(raw.decode(),r['path'],datetime.date.today());assert not errors and not warnings,(errors,warnings);p=D/'candidatos'/Path(r['path']).name;assert not p.exists();p.write_bytes(raw);r.update(candidato=str(p.relative_to(ROOT)),sha256_candidato=sha(raw),sha256_html=sha(src),sha256_metadados=sha(mdraw),metadados_raw=mdraw.decode(),HTML_normativo_normalizado=norm,normalizacao_administrativa=admin,fecho_proprio=closing[0],guard_sha256=snapshot['guard_sha256'],QA_codigo_sha256=sha(Path(__file__).read_bytes()));rows.append(r);render.append({'path':r['path'],'markdown':body})
 except Exception as e:r['motivo']=str(e);held.append(r)
(D/'preparo.json').write_text(json.dumps({'snapshot_respostas':len(results),'registros':rows,'retidos':held},ensure_ascii=False,indent=2)+'\n');code="import {marked} from '/Users/joaodavisn/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/marked/lib/marked.esm.js';let t='';for await(const x of process.stdin)t+=x;process.stdout.write(JSON.stringify(JSON.parse(t).map(r=>({path:r.path,html:marked.parse(r.markdown,{gfm:true,pedantic:false,breaks:false})}))));";outputs=json.loads(subprocess.check_output(['node','--input-type=module','-e',code],input=json.dumps(render).encode()));marked={r['path']:r['html'] for r in outputs};cm=MarkdownIt('commonmark',{'html':True,'linkify':False,'typographer':False});out=[]
for r,payload in zip(rows,render):
 sp=Visivel();sp.feed(r['HTML_normativo_normalizado']);a=v.texto_visivel_html(r['HTML_normativo_normalizado']);checks={};proof={}
 for engine,h in [('marked17',marked[r['path']]),('commonmark_markdown_it4',cm.render(payload['markdown']))]:
  mp=Visivel();mp.feed(h);b=v.texto_visivel_html(h);checks[engine]={'texto_pontuacao':a==b,'assinatura_numerica':v.assinatura_numerica(a)==v.assinatura_numerica(b),'contextos_numericos':contexto_numerico(a)==contexto_numerico(b),'matriz_tabelas':sp.structure==mp.structure,'sem_novas_listas':not re.search(r'<(?:ol|ul|li)\b',h,re.I),'sem_objetos_visuais':not mp.visual};proof[engine]={'html_renderizado':h,'sha256_html_renderizado':sha(h.encode()),'texto_visivel':b}
 out.append({'path':r['path'],'sha256_candidato':r['sha256_candidato'],'aprovado':all(all(x.values()) for x in checks.values()),'checks':checks,'texto_visivel_fonte':a,'renders':proof})
summary={'respostas_concluidas_no_snapshot':len(results),'fila_total':2000,'fontes_capturadas':sum(r['estado']=='fonte_capturada_para_QA' for r in results),'candidatos_preparo':len(rows),'retidos_preparo':len(held),'replay_aprovados':sum(r['aprovado'] for r in out),'replay_divergencias':sum(not r['aprovado'] for r in out),'promovidos':0};(D/'replay.json').write_text(json.dumps({'resumo':summary,'registros':out,'limites':'Snapshot privado, não seleção publicada. Pontuação, números e tabelas comparados em dois motores; sem certificar vigência/CSS. HTML com listas e visuais exige revisão específica. Divergências e fontes parciais permanecem retidas.'},ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary),flush=True)

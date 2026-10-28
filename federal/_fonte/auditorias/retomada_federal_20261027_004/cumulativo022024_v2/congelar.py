from pathlib import Path
import json,gzip,hashlib,subprocess,re,sys,importlib.util,collections,datetime
D=Path(__file__).resolve().parent;ROOT=D.parents[4];B=D.parent;sys.path.insert(0,str(ROOT/'scripts'));from preparar_lote_decretos_cache import fields
from identidade_decreto import numero_normalizado
from estados.pe_fidelidade_visivel import texto_visivel_html
from integridade_html_federal import Visivel
sha=lambda b:hashlib.sha256(b).hexdigest();prepared=json.loads((D/'preparo.json').read_text());qa=json.loads((D/'resultado.json').read_text());assert qa['resumo']=={'auditados':3848,'aprovados':3848,'divergencias':0};head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();tree=subprocess.check_output(['git','ls-tree','-rz',head,'--']+[f'federal/decretos/{y}' for y in [1939,1940,1941,1942]],cwd=ROOT);existing=set()
for row in tree.split(b'\0'):
 if not row:continue
 p=row.split(b'\t',1)[1].decode();m=re.fullmatch(r'federal/decretos/(\d{4})/dec-(.+)-\d{4}-\d\d-\d\d.md',p)
 if m:existing.add((numero_normalizado(m[2]),m[1]))
spec=importlib.util.spec_from_file_location('private_guard_biblio',ROOT/'federal/_proposta_guard_bibliografia_20261027_001/integridade_anexos_decreto.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard);seen=set();urns=set();rows=[];inventory=[];native=[];prom=[]
for r in prepared['publicaveis']:
 p=r['path'];key=(numero_normalizado(r['epigrafe']['numero']),r['epigrafe']['data'][:4]);assert key not in seen and key not in existing and r['urn'] not in urns;seen.add(key);urns.add(r['urn']);raw=(ROOT/r['arquivo_final']).read_bytes();assert sha(raw)==r['sha256'];old=(ROOT/p).read_bytes();assert sha(old)==r['sha256_preimagem'];sp=p.replace('federal/decretos/','federal/_fonte/decretos/').replace('.md','.html.gz');html=gzip.decompress((ROOT/sp).read_bytes());api=gzip.decompress((ROOT/r['captura_metadados']).read_bytes());assert sha(html)==r['sha256_fonte_html'] and sha(api)==r['sha256_metadados'];parsed=Visivel();parsed.feed(html.decode());alert=guard.anexo_proprio_ausente(fields(raw.decode())[2],parsed);assert not alert,(p,alert);v=texto_visivel_html(html.decode())
 for m in re.finditer(r'ileg[ií]vel|desenhos?\s+anexos?|(?:<<|«)\s*(?:anexo|tabela|quadro)s?\s*(?:>>|»)',v,re.I):inventory.append({'path':p,'sha256_md':sha(raw),'sha256_html':sha(html),'trecho':v[max(0,m.start()-400):m.end()+400]})
 rows.append({'path':p,'arquivo_final':r['arquivo_final'],'urn':r['urn'],'numero':r['epigrafe']['numero'],'data':r['epigrafe']['data'],'sha256_md_final':sha(raw),'sha256_preimagem':sha(old),'sha256_html':sha(html),'sha256_metadados':sha(api),'fonte_html_cache':sp,'captura_metadados':r['captura_metadados'],'fonte':r['fonte'],'url_texto':r['url_texto'],'lote':r['lote']})
 if r['arquivo_final']!=p:prom.append({'path':p,'candidate':r['arquivo_final'],'sha256_preimagem':sha(old),'sha256_candidato':sha(raw),'HTML_original':r['HTML_original']})
 if r['HTML_original']:native.append({'path':p,'candidato':r['arquivo_final'],'sha256_candidato':sha(raw),'fonte_html_cache':sp,'sha256_html':sha(html),'fonte_html_decodificada':html.decode(),'md_candidato_utf8':raw.decode()})
assert not inventory and len(prom)==191 and len(native)==12
(D/'verificacao3848.json').write_text(json.dumps({'HEAD_dedup':head,'sha256_arvore_scopo':sha(tree),'resumo':{'publicaveis_privados':len(rows),'retidos':len(prepared['retidos']),'promocoes':len(prom),'HTML_nativos':len(native),'replay_commonmark_divergencias':0,'alertas_guard_bibliografia_privado':0},'guard_bibliografia_sha256':sha((ROOT/'federal/_proposta_guard_bibliografia_20261027_001/integridade_anexos_decreto.py').read_bytes()),'registros':rows},ensure_ascii=False,indent=2)+'\n');(D/'promocoes191.json').write_text(json.dumps({'substituicoes':prom,'executadas':0,'limites':'ROOT valida preimagens e promove; este arquivo não altera canônicos.'},ensure_ascii=False,indent=2)+'\n');(D/'inventario_contextual3848.json').write_text(json.dumps({'resumo':{'corpos':3848,'ocorrencias':0},'registros':inventory,'limites':'Inventário lexical complementar; não equivale a revisão humana universal.'},ensure_ascii=False,indent=2)+'\n');(D/'nativos12_revisao_ROOT.json').write_text(json.dumps({'registros':native,'limites':'HTML normativo integral para leitura ROOT; replay local marcado passed, nenhuma chamada GitHub extra realizada. Não afirma identidade visual CSS.'},ensure_ascii=False,indent=2)+'\n')
for n in [22,23,24]:
 pub=[]
 for r in prepared['publicaveis']:
  if r['lote']!=n:continue
  q={k:v for k,v in r.items() if k not in ['proof','arquivo_final','HTML_original']}
  if r['arquivo_final']!=r['path']:q['candidato_promocao']=r['arquivo_final']
  pub.append(q)
 ret=[r for r in prepared['retidos'] if r['lote']==n];p=ROOT/f'federal/_lote_dec_continuacao_20261020_{n:03}_v2.json';assert not p.exists();p.write_text(json.dumps({'lote':f'continuacao_{n:03}_v2','escopo':'Seleção cumulativa privada, posterior e separada de 9061 e 3608; canônicos e snapshots anteriores preservados.','resumo':{'candidatos':2000,'publicaveis_privados':len(pub),'retidos':len(ret)},'publicaveis':pub,'retidos':ret,'provas':{'replay':str((D/'resultado.json').relative_to(ROOT)),'verificacao':str((D/'verificacao3848.json').relative_to(ROOT)),'overlay':'federal/_overlay_contexto_integridade_022024_20261027_001.json'},'limites':'Dependente da leitura ROOT dos 12 HTML nativos e dos contextos de fechos; não promover automaticamente. Nenhum runner executado.'},ensure_ascii=False,indent=2)+'\n');print(n,len(pub),len(ret),flush=True)

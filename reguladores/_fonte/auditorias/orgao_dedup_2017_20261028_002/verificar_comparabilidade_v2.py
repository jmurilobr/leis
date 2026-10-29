"""Reavalia todos os candidatos contra índice completo e reservas explícitas."""
from pathlib import Path
import sys,json,gzip,hashlib,collections,re
R=Path.cwd();D=Path(__file__).resolve().parent;sys.path.insert(0,str(D/'codigo'));from gate_orgao import n
from identidade_cross_snapshot import number
sha=lambda b:hashlib.sha256(b).hexdigest();idx=json.loads(gzip.decompress((D/'indice_transversal_v2.json.gz').read_bytes()));ov=json.loads(gzip.decompress((D/'overlay5920.json.gz').read_bytes()));keys=collections.defaultdict(list);uris=collections.defaultdict(list);urls=collections.defaultdict(list)
for r in idx['registros']:
 keys[(r['tipo'],r['numero'],r['data'])].append({'path':r['path'],'OID':r['OID'],'origem_chave':r['origem_chave']})
for r in idx['registros']+idx['reservas']:
 if r.get('URN_literal'):uris[r['URN_literal']].append(r['path'])
 if r.get('fonte_literal'):urls[r['fonte_literal']].append(r['path'])
base=R/'reguladores/_fonte/auditorias/dou2017_federal_20261028_001';rows=[];counts=collections.Counter();parts=[]
regtypes={'portaria','resolucao','instrucao normativa','ato normativo','circular','deliberacao','provimento','recomendacao','sumula','decisao','carta circular'}
for pack,num in [('final1604_001',1604),('final2135_001',2135),('final2181_001',2181)]:
 m=json.loads((base/pack/f'manifesto{num}.json').read_bytes())
 for r in m['documentos']:
  meta=r['meta'];typ=idx['tipos_explicitamente_comparaveis'].get(n(meta['tipo']));literal=number(meta['numero']);key=(typ,literal,meta['data'])if typ and literal else None;matches=keys.get(key,[])if key else[];direct_uri=uris.get(meta.get('urn'),[])if meta.get('urn')else[];direct_url=urls.get(meta.get('fonte'),[])if meta.get('fonte')else[];status='tipo_federal_comparavel'if key else'reserva_tipo_numero_serie_inconclusivos';why=None
  if not typ and n(meta['tipo'])in regtypes:
   if re.search(r'\b(?:senado federal|congresso nacional|camara dos deputados)\b',n(meta.get('orgao',''))):why='Tipo regulatório genérico em órgão legislativo: não equivale automaticamente a RSF/RCN/RRC; reserva para identidade institucional.'
   else:status='serie_regulatoria_distinta_sem_alias_legislativo';why='Tipo regulatório primário não é convertido por semelhança em série legislativa federal. Dedup de órgão/tipo/número/data e URL já coberto pelo baseline reguladores.'
  if status=='reserva_tipo_numero_serie_inconclusivos'and why is None:why='Ausência de chave comparável explícita; conservar em revisão. Nenhuma inferência por sequência ou número semelhante.'
  counts[status]+=1;counts['coincidencias_por_chave']+=bool(matches);counts['coincidencias_URN_literal']+=bool(direct_uri);counts['coincidencias_URL_literal']+=bool(direct_url);rows.append({'path':r['path'],'tipo_literal':meta['tipo'],'numero_literal':meta['numero'],'data':meta['data'],'status':status,'motivo':why,'chave':list(key)if key else None,'coincidencias_federais':matches,'coincidencias_URN':direct_uri,'coincidencias_URL':direct_url})
olddup={r['path']for r in ov['registros']if r['coincidencias_federais']};newdup={r['path']for r in rows if r['coincidencias_federais']or r['coincidencias_URN']or r['coincidencias_URL']};newreserve={r['path']for r in rows if r['status']=='reserva_tipo_numero_serie_inconclusivos'};assert olddup==newdup and len(newdup)==80 and not newreserve
result={'HEAD_indice':idx['HEAD'],'cobertura_indice':{'canônicos':idx['MD_canonicos'],'fora_padrao_lidos_por_OID':idx['fora_padrao_filename_lidos_por_OID'],'reservas_canonicas_sem_chave':idx['reservados_sem_chave']},'contagens':counts,'sem_novas_exclusoes_apos_ampliar_indice':True,'registros':rows,'limites':'URN/URL cotejados quando presentes nos metadados lidos por OID; os demais canônicos com filename explícito são cotejados pela chave tipo/série+número/sufixo+data. Resoluções regulatórias não são fundidas em séries legislativas; candidatos sem identidade institucional seriam reservados. Nenhuma alteração ou máscara.'};(D/'comparabilidade5920_v2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='registros'},ensure_ascii=False),flush=True)

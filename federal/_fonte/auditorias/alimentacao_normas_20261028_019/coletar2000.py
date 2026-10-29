"""Coleta privada retomável, 2 rps globais/4 workers, sem conversão ou promoção."""
from pathlib import Path
import sys,json,gzip,hashlib,datetime,re,threading,fcntl,urllib.parse
from concurrent.futures import ThreadPoolExecutor,as_completed
B=Path(__file__).resolve().parent;ROOT=B.parents[3];sys.path.insert(0,str(ROOT/'scripts'));import baixar_federal as f
sha=lambda b:hashlib.sha256(b).hexdigest();lock=(B/'cliente.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
source=B/'proxima_faixa_normas2000_inventario.json';raw=source.read_bytes();qp=B/'fila2000.json'
if qp.exists():assert qp.read_bytes()==raw
else:qp.write_bytes(raw)
queue=json.loads(raw);assert len(queue['registros'])==2000;guard_sha=sha((ROOT/'scripts/integridade_anexos_decreto.py').read_bytes());sp=B/'snapshot_codigo.json';snapshot={'guard_sha256':guard_sha,'baixar_federal_sha256':sha((ROOT/'scripts/baixar_federal.py').read_bytes()),'coletor_sha256':sha(Path(__file__).read_bytes()),'fila_sha256':sha(raw),'rps':2,'workers':4,'limite_requisicoes_novas':4000}
if sp.exists():assert json.loads(sp.read_bytes())==snapshot
else:sp.write_text(json.dumps(snapshot,indent=2)+'\n')
for name in ['requests','resultados','preexistentes']:(B/name).mkdir(exist_ok=True)
f.LIMITE=f.Limitador(2);stop=threading.Event();mutex=threading.Lock();url_locks={};count=0

def atomic(p,data):
 try:
  t=p.with_name(p.name+f'.{threading.get_ident()}.tmp');t.write_bytes(data);t.replace(p)
 except OSError:
  stop.set();raise
def jwrite(p,value):atomic(p,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
def obtain(url,accept):
 global count
 assert urllib.parse.urlparse(url).hostname in {'normas.leg.br','legis.senado.leg.br'},url
 with mutex:
  if url not in url_locks:url_locks[url]=threading.Lock()
  url_lock=url_locks[url]
 with url_lock:
  key=sha(url.encode());p=B/'requests'/(key+'.raw.gz');rp=B/'requests'/(key+'.json')
  if rp.exists():
   receipt=json.loads(rp.read_bytes());body=gzip.decompress(p.read_bytes());assert receipt['url']==url and receipt.get('accept')==accept and sha(body)==receipt['sha256_raw'];assert receipt['status_http']==200 and body,'Cache sem conteúdo válido; não repetir captura';return body,receipt
  prior_dirs=[ROOT/f'federal/_fonte/auditorias/alimentacao_normas_{20261028 if n>=14 else 20261027}_{n:03}/requests' for n in [18,17,16,15,14,13,12,11,10,9,8]];prior=next((p for p in prior_dirs if (p/(key+'.json')).exists() or (p/(key+'.erro.json')).exists()),prior_dirs[0]);prior_receipt=prior/(key+'.json');prior_error=prior/(key+'.erro.json')
  if prior_receipt.exists():
   old=json.loads(prior_receipt.read_bytes());body=gzip.decompress((prior/(key+'.raw.gz')).read_bytes());assert old['url']==url and old.get('accept')==accept and sha(body)==old['sha256_raw'];receipt={**old,'origem':'cache de requisição oficial anterior, sem novo HTTP','arquivo_raw':str(p.relative_to(ROOT)),'recibo_anterior':str(prior_receipt.relative_to(ROOT)),'sha256_recibo_anterior':sha(prior_receipt.read_bytes())};atomic(p,gzip.compress(body,mtime=0));jwrite(rp,receipt);assert receipt['status_http']==200 and body,'Cache oficial anterior sem conteúdo; retido sem repetir';return body,receipt
  if prior_error.exists():
   old=json.loads(prior_error.read_bytes())
   if old.get('recusa_suspende_cliente'):stop.set()
   raise RuntimeError('Falha anterior preservada, sem repetir requisição: '+str(prior_error.relative_to(ROOT)))
  if stop.is_set():raise RuntimeError('Cliente suspenso por recusa; nenhuma nova requisição')
  with mutex:assert count<4000;count+=1
  receipt={'url':url,'accept':accept,'captura_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'origem':'captura oficial nova em cliente único a 2 rps, sem retry'}
  try:status,body=f.http_get(url,accept,tentativas=1)
  except Exception as e:
   receipt.update(erro=str(e),estado='falha')
   if re.search(r'HTTP (?:401|403|429)',str(e)):stop.set();receipt['recusa_suspende_cliente']=True
   jwrite(rp.with_suffix('.erro.json'),receipt);raise
  receipt.update(status_http=status,arquivo_raw=str(p.relative_to(ROOT)),sha256_raw=sha(body),bytes=len(body));atomic(p,gzip.compress(body,mtime=0));jwrite(rp,receipt)
  if any(t in body[:300000].lower() for t in [b'verify you are human',b'captcha-container',b'<title>access denied',b'403 forbidden',b'429 too many requests']):stop.set();raise RuntimeError('Recusa textual da fonte; cliente suspenso')
  assert status==200 and body,'HTTP sem conteúdo válido'
  return body,receipt

def worker(row):
 if stop.is_set():return {'path':row['path'],'urn':row['urn'],'estado':'nao_tentado_suspenso'}
 key=sha(row['urn'].encode());rp=B/'resultados'/(key+'.json')
 if rp.exists():
  r=json.loads(rp.read_bytes());assert r['path']==row['path'];return r
 r={'path':row['path'],'urn':row['urn'],'indice':row['indice'],'estado':'iniciado'}
 try:
  if row['HTML_preexistente']:
   p=ROOT/row['HTML_preexistente'];body=gzip.decompress(p.read_bytes());snapshot=B/'preexistentes'/(key+'.html.gz');atomic(snapshot,gzip.compress(body,mtime=0));r.update(estado='retido_cache_preexistente',HTML_preexistente_preservado=str(snapshot.relative_to(ROOT)),sha256_html_preexistente=sha(body),motivo='HTML preexistente separado para QA específico e prova de edição; não capturar novamente nem presumir autoria ou integridade.',diagnostico='federal/_fonte/auditorias/alimentacao_20261027_007/diagnostico13_cache_preexistente.json');jwrite(rp,r);return r
  cached=row['metadados_preexistentes']
  if cached:
   assert len(cached)==1,'Múltiplas capturas API preexistentes exigem revisão sem escolher pelo hash';cp=cached[0];metaraw=gzip.decompress((ROOT/cp['path']).read_bytes());assert sha(metaraw)==cp['sha256_raw'];p=B/'preexistentes'/(key+'.json.gz');atomic(p,gzip.compress(metaraw,mtime=0));r['metadados']={'origem':'cache preexistente, autoria não presumida','arquivo_raw':str(p.relative_to(ROOT)),'sha256_raw':sha(metaraw),'fonte_anterior':cp['path']}
  else:metaraw,r['metadados']=obtain(f.API_NORMA.format(urllib.parse.quote(row['urn'],safe=':;@!~$-.')),'application/json')
  meta=json.loads(metaraw);assert meta.get('legislationIdentifier')==row['urn'],'URN API diverge: exige fonte alternativa e revisão de identidade';day,month,year=row['indice']['dataassinatura'].split('/');assert meta.get('legislationDate')==f'{year}-{month}-{day}' and meta.get('legislationType') in {'Decreto','Decreto Numerado'},'Data/tipo API diverge do índice'
  enc=f.escolher_texto(meta)
  if not enc:r.update(estado='sem_encoding_API',motivo='Metadados oficiais preservados; nenhuma nova consulta ao corpo ou ao Senado. Não implica inexistência do ato.');jwrite(rp,r);return r
  assert enc.get('version') in {'Original','Current'},'Edição intermediária exige revisão; não coletada como íntegra'
  url=enc['contentUrl'].replace('/api/binario/','/api/public/binario/');body,r['texto']=obtain(url,'text/html');r['encoding_escolhido']=enc;r['estado']='fonte_capturada_para_QA';r['tipo_real']='PDF' if body.startswith(b'%PDF') else 'HTML';r['limites']='A captura não certifica identidade, íntegra, anexos, fidelidade ou vigência. Nenhum candidato ou destino MD criado.'
 except Exception as e:r.update(estado='retido_coleta',motivo=str(e))
 jwrite(rp,r);return r
results=[]
with ThreadPoolExecutor(max_workers=4) as pool:
 futures=[pool.submit(worker,r) for r in queue['registros']]
 for future in as_completed(futures):
  results.append(future.result())
  if len(results)%20==0 or len(results)==2000:
   summary={'concluidos':len(results),'fila':2000,'fontes_capturadas':sum(r['estado']=='fonte_capturada_para_QA' for r in results),'sem_encoding_API':sum(r['estado']=='sem_encoding_API' for r in results),'retidos_cache':sum(r['estado']=='retido_cache_preexistente' for r in results),'retidos_coleta':sum(r['estado']=='retido_coleta' for r in results),'requisicoes_novas_nesta_execucao':count,'recusa':stop.is_set()};jwrite(B/'checkpoint.json',{'snapshot':snapshot,'resumo':summary,'registros':results});print(summary,flush=True)
print('FIM: sem processos filhos ou promoção. Retomável por recibo de URL e resultado por URN.',flush=True)

from pathlib import Path
import json,gzip,hashlib,sys,re,html,urllib.parse,datetime,fcntl
B=Path(__file__).resolve().parent;ROOT=B.parents[3];sys.path.insert(0,str(ROOT/'scripts'));import baixar_federal as f
from comum import decodificar
sha=lambda b:hashlib.sha256(b).hexdigest();f.LIMITE=f.Limitador(1);D=B/'capturas';D.mkdir(exist_ok=True);lock=(B/'cliente.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
queue=json.loads((B/'fila_camara200.json').read_bytes());assert sha((ROOT/'scripts/integridade_anexos_decreto.py').read_bytes())==queue['guard_sha256'];records=[];requests=0;blocked=False

def atomic(p,raw):
 t=p.with_name(p.name+'.tmp');t.write_bytes(raw);t.replace(p)
def save():atomic(B/'checkpoint_coleta.json',(json.dumps({'fila_sha256':sha((B/'fila_camara200.json').read_bytes()),'rps':1,'cliente_unico':True,'limite_candidatos':200,'requisicoes_novas_nesta_execucao':requests,'bloqueio':blocked,'registros':records},ensure_ascii=False,indent=2)+'\n').encode())
def obtain(url):
 global requests,blocked
 assert urllib.parse.urlparse(url).hostname in {'www.camara.leg.br','www2.camara.leg.br'}
 assert not blocked
 key=sha(url.encode());p=D/(key+'.html.gz');rp=D/(key+'.json')
 if rp.exists():
  r=json.loads(rp.read_bytes());raw=gzip.decompress(p.read_bytes());assert r['url']==url and sha(raw)==r['sha256_raw'];s=decodificar(raw,'text/html');assert sha(s.encode())==r['sha256_decodificado'];return s,r
 previous=ROOT/'federal/_fonte/camara'/(key+'.html.gz');r={'url':url,'captura_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 if previous.exists():raw=gzip.decompress(previous.read_bytes());status=200;s=raw.decode('utf-8');r['origem']='cache preexistente, autoria não presumida'
 else:
  assert requests<600;requests+=1
  try:status,raw=f.http_get(url,'text/html',tentativas=1)
  except Exception as e:
   if re.search(r'HTTP (?:401|403|429)',str(e)):blocked=True
   raise
  s=decodificar(raw,'text/html');r['origem']='captura oficial nova, cliente limitado'
 r.update(status_http=status,arquivo=str(p.relative_to(ROOT)),sha256_raw=sha(raw),sha256_decodificado=sha(s.encode()),bytes=len(raw));atomic(p,gzip.compress(raw,mtime=0));atomic(rp,(json.dumps(r,ensure_ascii=False,indent=2)+'\n').encode())
 if any(x in s.lower() for x in ['verify you are human','verifique que você é humano','captcha-container']):blocked=True;raise RuntimeError('Fonte recusou em HTML; cliente suspenso')
 assert status==200 and raw
 return s,r
for candidate in queue['candidatos']:
 if blocked:break
 n=str(candidate['indice']['numero']);y=str(candidate['indice']['anoassinatura']);p=B/(n+'-resultado.json')
 if p.exists():records.append(json.loads(p.read_bytes()));save();continue
 r={'path_alvo':candidate['path'],'numero':n,'ano':y,'urn':candidate['detalhe']['urn'],'estado':'iniciado'}
 try:
  url='https://www.camara.leg.br/legislacao/busca?'+urllib.parse.urlencode({'tipo':'Decreto','ordenacao':'data:DESC','pagina':1,'ano':int(y),'numero':int(n)});s,proof=obtain(url);r['busca']=proof
  total=re.search(r'Exibindo resultados de\s+[\d.]+\s+a\s+[\d.]+\s+de\s+([\d.]+)',s);r['total_reconhecido']=int(total[1].replace('.','')) if total else None;docs=[]
  for item in re.findall(r'<li class="busca-resultados__item[^\"]*">(.*?)</li>',s,re.S):
   a=re.search(r'<a[^>]+href="([^"]+/legin/[^"]+)"[^>]*>(.*?)</a>',item,re.S)
   if a:docs.append({'url':html.unescape(a[1]),'titulo':' '.join(html.unescape(re.sub('<[^>]+>',' ',a[2])).split())})
  r['documentos']=docs
  if r['total_reconhecido']!=1 or len(docs)!=1:raise ValueError('Busca não individualiza exatamente um documento; exige revisão, sem presumir inexistência')
  doc=docs[0];page,pr=obtain(doc['url']);r['pagina_norma']=pr;ident=re.search(r'-(\d+)-norma',doc['url'])[1];links=[html.unescape(u) for u in re.findall(r'href=["\']([^"\']+)["\']',page)];originals=list(dict.fromkeys(urllib.parse.urljoin(doc['url'],u) for marker in ['-publicacaooriginal-','-textopublicacaooriginal-'] for u in links if marker in u and '-'+ident+'-' in u and u.lower().endswith('.html')));r['originais_observados']=originals
  if not originals:raise ValueError('Nenhum HTML Original observado; preserva página para fonte alternativa')
  body,pr=obtain(originals[0]);r['texto_original']=pr;r['estado']='capturado_para_QA_sem_promocao'
 except Exception as e:r['estado']='retido_coleta';r['erro']=str(e)
 atomic(p,(json.dumps(r,ensure_ascii=False,indent=2)+'\n').encode());records.append(r);save();print(len(records),'/200',n,r['estado'],'HTTP novos',requests,'bloqueio',blocked,flush=True)
save();print('FIM',len(records),'capturados',sum(r['estado']=='capturado_para_QA_sem_promocao' for r in records),'bloqueio',blocked,flush=True)

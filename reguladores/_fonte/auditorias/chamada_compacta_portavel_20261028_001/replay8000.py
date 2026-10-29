"""Replay portátil somente leitura do delta lexical integral, sem rede/caches."""
from pathlib import Path
import sys,json,gzip,hashlib,urllib.request
B=Path(__file__).resolve().parent;R=B.parents[3];G=B.with_name('chamada_compacta_20261028_001');C=B.with_name('orgao_dedup_2017_20261028_002')/'codigo';sys.path[:0]=[str(G),str(C)];sha=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((B/'manifesto8000.json').read_bytes());assert sha((R/m['gate']['path']).read_bytes())==m['gate']['sha256']
for path,digest in m['codigos'].items():assert sha((R/path).read_bytes())==digest,path
def sem_http(*a,**kw):raise AssertionError('HTTP proibido no replay')
urllib.request.urlopen=sem_http
from gate_chamada_compacta import chamadas
from auditar_cache_dou import meta_corpo
by={r['path']:r for r in m['registros']};done=[];hits=[]
for part in m['partes']:
 p=R/part['path'];compressed=p.read_bytes();assert sha(compressed)==part['sha256_gzip'];n=0;offset=0
 for line in gzip.open(p,'rb'):
  r=json.loads(line);row=by[r['path']];raw=r['MD_UTF8'].encode();member=compressed[row['offset_gzip']:row['offset_gzip']+row['bytes_member']];assert row['offset_gzip']==offset and sha(member)==row['sha256_member']and gzip.decompress(member)==line;offset+=row['bytes_member'];assert sha(raw)==r['sha256_MD']==row['sha256_MD']and len(raw)==row['bytes_MD'];assert r['indice']==row['indice'];meta,body=meta_corpo(raw.decode());alerts=chamadas(body);done.append(r['path']);n+=1
  if alerts:hits.append({'path':r['path'],'sha256_MD':sha(raw),'chamadas':alerts})
 assert n==part['registros']and offset==len(compressed)
assert len(done)==len(set(done))==8000 and set(done)==set(by);expected=json.loads((G/'delta8000.json').read_bytes())['registros'];assert{r['path']for r in hits}=={r['path']for r in expected}and len(hits)==2
for h in hits:assert h['sha256_MD']==next(r['sha256_MD']for r in expected if r['path']==h['path'])
proofs=[json.loads(l)for l in gzip.decompress((G/'provas_delta8000.jsonl.gz').read_bytes()).splitlines()]
for p in proofs:assert sha(p['MD_utf8'].encode())==p['registro']['sha256_MD']and sha(p['HTML_utf8'].encode())==p['registro']['sha256_HTML']
control=json.loads(gzip.decompress((G/'controle_MDS43.json.gz').read_bytes()));assert sha(control['MD_utf8'].encode())==control['sha256_MD']and sha(control['HTML_utf8'].encode())==control['sha256_HTML'];assert not chamadas(meta_corpo(control['MD_utf8'])[1]);print(json.dumps({'corpos_completos_reproduzidos':8000,'alertas_compactos':2,'controle_prospectivo_sem_alerta':True,'escritas':0,'HTTP':0,'limites':'Reproduz o predicado lexical específico no corpo exato; não certifica ausência/integralidade de todas as normas nem revisão humana universal.'},ensure_ascii=False))

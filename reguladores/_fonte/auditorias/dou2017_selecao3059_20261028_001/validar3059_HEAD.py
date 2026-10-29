"""Pré-publicação somente leitura, com delta explícito dos dois corpora HEAD."""
from pathlib import Path
import sys,json,gzip,hashlib,subprocess,threading,collections,re
D=Path(__file__).resolve().parent;R=next(p for p in D.parents if(p/'scripts').is_dir()and(p/'reguladores').is_dir());sys.path.insert(0,str(R/'reguladores/_fonte/auditorias/orgao_dedup_2017_20261028_002/codigo'));from gate_orgao import n
from identidade_cross_snapshot import number
from gates_snapshot import chave
sha=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((D/'manifesto3059.json').read_bytes());idx=json.loads(gzip.decompress((R/m['baseline_federal']['path']).read_bytes()));base=json.loads(gzip.decompress((R/m['baseline_reguladores']['path']).read_bytes()));docs={r['path']:r for r in base['documentos']};federal={r['path']:r for r in idx['registros']+idx['reservas']};head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();changes=[];counts=collections.Counter()
for scope,previous in [('reguladores',base['HEAD']),('federal',idx['HEAD'])]:
 delta=subprocess.check_output(['git','diff','--name-status','-z',previous,head,'--',scope],cwd=R).decode().split('\0');i=0
 while i<len(delta)and delta[i]:
  status,path=delta[i:i+2];i+=2;assert not status.startswith(('R','C')),'Renomeação requer reconciliação específica'
  if not path.endswith('.md')or any(p.startswith('_')for p in Path(path).parts):continue
  counts[scope+'_delta_MD']+=1
  if status=='D':(docs if scope=='reguladores'else federal).pop(path,None)
  else:changes.append((scope,path))
proc=subprocess.Popen(['git','cat-file','--batch'],cwd=R,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
def feed():
 for scope,path in changes:proc.stdin.write((head+':'+path+'\n').encode())
 proc.stdin.close()
t=threading.Thread(target=feed);t.start()
for scope,path in changes:
 h=proc.stdout.readline().split();assert len(h)==3 and h[1]==b'blob';raw=proc.stdout.read(int(h[2]));assert proc.stdout.read(1)==b'\n';assert raw.startswith(b'---\n')and b'\n---\n'in raw[4:];meta={}
 for line in raw[4:].split(b'\n---\n',1)[0].decode().splitlines():
  k,sep,v=line.partition(':')
  if sep:
   v=v.strip()
   try:meta[k]=json.loads(v)
   except ValueError:meta[k]=v
 if scope=='reguladores':docs[path]={'path':path,'meta':meta}
 else:
  typ=idx['tipos_explicitamente_comparaveis'].get(n(meta.get('tipo','')));num=number(meta.get('numero',''));date=meta.get('data');row={'path':path,'OID':h[0].decode(),'sha256_MD_HEAD':sha(raw),'URN_literal':meta.get('urn'),'fonte_literal':meta.get('fonte')}
  if typ and num and re.fullmatch(r'\d{4}-\d\d-\d\d',str(date or'')):row.update(tipo=typ,numero=num,data=date)
  else:row['reserva_sem_chave']=True
  federal[path]=row
t.join();assert proc.wait()==0;keys={chave(x['meta'],x['path'])for x in docs.values()};urls={x['meta'].get('fonte')for x in docs.values()};fk={(x['tipo'],x['numero'],x['data'])for x in federal.values()if'tipo'in x};fu={x.get('URN_literal')for x in federal.values()if x.get('URN_literal')};fs={x.get('fonte_literal')for x in federal.values()if x.get('fonte_literal')};selected=m['documentos'];assert len(selected)==3059;check=subprocess.check_output(['git','cat-file','--batch-check'],cwd=R,input=''.join(head+':'+x['path']+'\n'for x in selected).encode()).decode().splitlines();assert len(check)==3059
for r,line in zip(selected,check):
 path=r['path'];meta=r['meta'];assert line==head+':'+path+' missing',path;assert path not in docs and chave(meta,path)not in keys and meta['fonte']not in urls,path;assert sha((R/path).read_bytes())==r['sha256_md'],path;typ=idx['tipos_explicitamente_comparaveis'].get(n(meta['tipo']));num=number(meta['numero']);assert not(typ and num)or(typ,num,meta['data'])not in fk,path;assert not meta.get('urn')or meta['urn']not in fu;assert meta['fonte']not in fs;keys.add(chave(meta,path));urls.add(meta['fonte'])
print(json.dumps({'HEAD':head,'MD_reguladores_publicos_reconciliados':len(docs),'MD_federais_cobertos_ou_reservados':len(federal),'deltas_MD_por_corpus':counts,'selecionados_ineditos_path_identidade_URL_e_transversal':3059,'MD_preexistentes_SHA_exatos':3059,'escritas':0,'limites':'Reservas sem chave continuam explícitas; não é dedup universal. Tipo/série/número/sufixo/data só são comparados quando inequívocos.'},ensure_ascii=False))

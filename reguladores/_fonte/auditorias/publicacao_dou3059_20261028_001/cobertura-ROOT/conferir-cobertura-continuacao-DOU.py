from pathlib import Path
import gzip,json,subprocess,hashlib,threading,time
sha=lambda b:hashlib.sha256(b).hexdigest();B=Path('reguladores/_fonte/auditorias/dou2017_continuacao_20261028_001');expected_sha={'indice_federal_HEAD_reservas.json.gz':'cc1ed0d878154dcbfaa4747405e095d01ea308d383def94631fa6fb0dc28af24','baseline_reguladores_HEAD_reservas.json.gz':'709f5719b36aabaca7e52fe970ed23c51bca7f84220129b09b855a95451644d8'}
for name,d in expected_sha.items():assert sha((B/name).read_bytes())==d
idx=json.loads(gzip.decompress((B/'indice_federal_HEAD_reservas.json.gz').read_bytes()));reg=json.loads(gzip.decompress((B/'baseline_reguladores_HEAD_reservas.json.gz').read_bytes()));fed={r['path']:r for r in idx['registros']+idx['reservas']};regs={r['path']:r for r in reg['documentos']};assert len(fed)==190834 and len(regs)==270389;assert len(idx['reservas'])==14615;assert all(p not in regs for p in fed);head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();tree=subprocess.check_output(['git','ls-tree','-rz',head,'--','federal','reguladores']);actual={}
for rec in tree.split(b'\0'):
 if not rec:continue
 data,p=rec.split(b'\t',1);path=p.decode();mode,typ,oid=data.split()
 if typ==b'blob' and path.endswith('.md') and not any(x.startswith('_') for x in Path(path).parts):assert mode==b'100644';actual[path]=oid.decode()
assert set(actual)==set(fed)|set(regs),(len(actual),len(fed),len(regs));items=[(p,'federal',r) for p,r in fed.items()]+[(p,'reguladores',r) for p,r in regs.items()];proc=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
def feed():
 for p,scope,r in items:proc.stdin.write((actual[p]+'\n').encode())
 proc.stdin.close()
t=threading.Thread(target=feed);t.start();O=Path('_fonte/operacao_root_20261027/cobertura-continuacao-DOU-ROOT');O.mkdir(exist_ok=False);files={s:O/(s+'-blobs.jsonl.gz') for s in ['federal','reguladores']};streams={s:gzip.GzipFile(filename=str(p),mode='wb',mtime=0) for s,p in files.items()};counts={'federal':0,'reguladores':0};fields=0;private=0
for pos,(p,scope,r) in enumerate(items,1):
 line=proc.stdout.readline().split();assert len(line)==3 and line[0].decode()==actual[p] and line[1]==b'blob';raw=proc.stdout.read(int(line[2]));assert proc.stdout.read(1)==b'\n';digest=sha(raw);header=raw[4:].split(b'\n---\n',1)[0].decode() if raw.startswith(b'---\n') and b'\n---\n' in raw[4:] else None;meta={}
 if header is not None:
  for ln in header.splitlines():
   k,sep,value=ln.partition(':')
   if sep:
    value=value.strip()
    try:meta[k]=json.loads(value)
    except ValueError:meta[k]=value
 if scope=='reguladores':
  for k,v in r['meta'].items():assert meta.get(k)==v,(p,k,meta.get(k),v);fields+=1
 else:
  if r.get('OID') is not None:assert r['OID']==actual[p],p
  for key in ['sha256_MD_HEAD','sha256_MD']:
   if key in r:assert r[key]==digest,(p,key)
  if r.get('meta_LITERAL') is not None:assert meta==r['meta_LITERAL'],p
  for stored,key in [('URN_literal','urn'),('fonte_literal','fonte')]:
   if stored in r:assert meta.get(key)==r[stored],(p,key)
  if r.get('reserva_privada'):private+=1
 streams[scope].write((json.dumps({'path':p,'OID':actual[p],'sha256_MD_HEAD':digest,'bytes_MD_HEAD':len(raw),'sha256_cabecalho_integral':sha(header.encode()) if header is not None else None},ensure_ascii=False,separators=(',',':'))+'\n').encode());counts[scope]+=1
 if pos%50000==0:print({'blobs_integrais_lidos':pos,'por_corpus':counts},flush=True)
t.join();assert proc.wait()==0
for f in streams.values():f.close()
assert head==subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();out={'HEAD':head,'HEAD_declarado_nos_indices':idx['HEAD'],'indices_SHA':expected_sha,'blobs_integrais_por_OID':counts,'canonicos_exatos_total':len(actual),'campos_reguladores_conferidos':fields,'federais_com_chave':len(idx['registros']),'reservas_sem_chave':len(idx['reservas']),'reservas_privadas_federais_agora_no_HEAD':private,'reservas_reguladores_restantes':0,'arquivos_prova':[{ 'path':str(p),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in files.values()],'criterio':'ROOT conferiu conjunto exato dos dois corpora HEAD e leu integralmente todos461223 blobs por OID. Metadados de todos reguladores comparados campo a campo ao índice; OIDs/SHA/metadados/URN/URL federais quando declarados conferidos, incluindo reservas futuras agora publicadas. Estatísticas antigas189008/174393 do índice são antecedentes; cobertura efetiva190834/176219/14615. Nenhum candidato selecionado é aprovado por esta prova de cobertura; replay e dedup separados continuam necessários. Não é dedup universal ou certificado de vigência.'};q=O/'recibo.json';q.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(out,flush=True)

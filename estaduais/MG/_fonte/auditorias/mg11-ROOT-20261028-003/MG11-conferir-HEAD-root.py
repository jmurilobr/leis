from pathlib import Path
import subprocess,json,hashlib,gzip,threading,re,unicodedata,urllib.parse
sha=lambda b:hashlib.sha256(b).hexdigest();B=Path('estaduais/MG/_fonte/auditorias/mg11-proposta-privada-20261028-002');m=json.loads((B/'manifesto.json').read_bytes());head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();tree=subprocess.check_output(['git','ls-tree','-rz',head,'--','estaduais/MG/decretos','estaduais/MG/resolucoes']);assert tree==Path(m['tree']).read_bytes();actual={}
for entry in tree.split(b'\0'):
 if not entry:continue
 a,p=entry.split(b'\t',1);path=p.decode();mode,typ,oid=a.split()
 if typ==b'blob' and path.endswith('.md') and not any(x.startswith('_') for x in Path(path).parts):assert mode==b'100644';actual[path]=oid.decode()
assert len(actual)==47972
normalize=lambda s:''.join(c for c in unicodedata.normalize('NFD',str(s).lower()) if not unicodedata.combining(c))
def metadata(raw):
 assert raw.startswith(b'---\n') and b'\n---\n' in raw[4:];header=raw[4:].split(b'\n---\n',1)[0].decode();meta={}
 for line in header.splitlines():
  k,sep,v=line.partition(':')
  if sep:
   v=v.strip()
   try:meta[k]=json.loads(v)
   except ValueError:meta[k]=v
 return meta,header

def number(n):
 n=re.sub(r'[.\s]','',str(n)).upper();match=re.fullmatch(r'(\d+)(.*)',n)
 return (str(int(match[1]))+match[2]) if match else n

def key(meta):return normalize(meta.get('tipo','')),number(meta.get('numero',''))
def official(meta):
 u=urllib.parse.urlsplit(str(meta.get('fonte','')));q=urllib.parse.parse_qs(u.query);hit=re.search(r'/(?:api/v2/legislacao/mineira|legislacao-mineira/texto)/([^/]+)/(\d+)/(\d{4})(?:/|$)',u.path)
 if u.hostname in ['dadosabertos.almg.gov.br','www.almg.gov.br','almg.gov.br'] and hit:return hit[1].upper(),number(hit[2]),hit[3],tuple(q.get('comp',[]))
 return None
candidates={};officials=set();paths=set()
for d in m['documentos']:
 raw=Path(d['candidato']).read_bytes();assert sha(raw)==d['sha256_md'] and raw==Path(d['path']).read_bytes();meta,_=metadata(raw);k=key(meta);assert k not in candidates and d['path'] not in paths;candidates[k]=d['path'];paths.add(d['path']);o=official(meta);assert o is not None and o not in officials;officials.add(o)
assert len(paths)==11;checks=subprocess.check_output(['git','cat-file','--batch-check'],input=''.join(head+':'+p+'\n'for p in paths).encode()).splitlines();assert len(checks)==11 and all(x.endswith(b' missing')for x in checks)
P=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE);items=list(actual.items())
def feed():
 for p,oid in items:P.stdin.write((oid+'\n').encode())
 P.stdin.close()
t=threading.Thread(target=feed);t.start();out=Path('_fonte/operacao_root_20261027/MG11-HEAD-blobs-root.jsonl.gz');assert not out.exists();f=gzip.GzipFile(filename=str(out),mode='wb',mtime=0);with_number=0
for p,oid in items:
 a=P.stdout.readline().split();assert len(a)==3 and a[0].decode()==oid and a[1]==b'blob';raw=P.stdout.read(int(a[2]));assert P.stdout.read(1)==b'\n';meta,header=metadata(raw);k=key(meta);assert k not in candidates,(p,k,candidates.get(k));o=official(meta);assert o is None or o not in officials,(p,o);with_number+=bool(meta.get('numero'));f.write((json.dumps({'path':p,'OID':oid,'sha256_MD':sha(raw),'bytes':len(raw),'sha256_cabecalho':sha(header.encode())},ensure_ascii=False,separators=(',',':'))+'\n').encode())
t.join();assert P.wait()==0;f.close();assert head==subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();result={'HEAD':head,'HEAD_manifesto':m['HEAD'],'blobs_MG_lidos_integrais_por_OID':len(actual),'com_numero_no_cabecalho':with_number,'candidatos':11,'colisoes_tipo_numero_sem_ano':0,'colisoes_recurso_oficial_ALMG':0,'destinos_ausentes_HEAD':11,'arvore_HEAD_byte_identica_ao_baseline':True,'prova_blobs':str(out),'sha256_prova':sha(out.read_bytes()),'limite':'ROOT conferiu todos os cabeçalhos reais por OID, não somente nomes de arquivo; número preserva sufixos e tipo distingue espécies. Endpoint oficial e CSV qualificam cada candidato separadamente. Nenhuma edição impressa/vigência atual universal certificada.'};q=Path('_fonte/operacao_root_20261027/MG11-HEAD-root.json');assert not q.exists();q.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result)

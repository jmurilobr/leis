"""Cobertura transversal por caminho e fallback de metadados lidos por OID."""
from pathlib import Path
import sys,re,json,gzip,hashlib,subprocess,threading,collections
R=Path.cwd();D=Path(__file__).resolve().parent;sys.path.insert(0,str(D/'codigo'));from gate_orgao import n
from identidade_cross_snapshot import types,number
sha=lambda b:hashlib.sha256(b).hexdigest();types={**types,'resolucao do senado federal':'rsf','resolucao do congresso nacional':'rcn','resolucao da camara dos deputados':'rrc'};series={'leis-ordinarias':('lei',{'lei'}),'leis-complementares':('lc',{'lcp'}),'medidas-provisorias':('mp',{'mpv'}),'decretos':('dec',{'dec'}),'decretos-lei':('del',{'del'}),'decretos-legislativos':('dlg',{'dlg','dpl'}),'emendas-constitucionais':('ec',{'emc','emr'}),'leis-delegadas':('ldl',{'ldl'}),'leis-constitucionais':('lct',{'lct'}),'resolucoes-senado':('rsf',{'rsf'}),'resolucoes-congresso':('rcn',{'rcn'}),'resolucoes-camara':('rrc',{'rrc'})};head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();rawtree=subprocess.check_output(['git','ls-tree','-rz',head,'--','federal']);tp=D/'federal_HEAD_tree_completo.z.gz';assert not tp.exists();tp.write_bytes(gzip.compress(rawtree,mtime=0));count=collections.defaultdict(collections.Counter);indexed=[];fallback=[];ignored=[]
for entry in rawtree.split(b'\0'):
 if not entry:continue
 descriptor,path=entry.split(b'\t',1);mode,kind,oid=descriptor.split();path=path.decode();parts=Path(path).parts
 if kind!=b'blob'or not path.endswith('.md'):continue
 if any(x.startswith('_')for x in parts):ignored.append({'path':path,'OID':oid.decode(),'motivo':'Artefato de fonte/prova em diretório reservado; não canônico normativo'});continue
 directory=parts[1]if len(parts)>2 else'(raiz federal)';count[directory]['MD_canonicos']+=1;row={'path':path,'OID':oid.decode(),'diretorio':directory};m=re.fullmatch(r'([a-z]+)-(.+)-(\d{4}-\d\d-\d\d)\.md',parts[-1]);spec=series.get(directory)
 if len(parts)==4 and m and spec and m[1]in spec[1]and number(m[2]):
  typ='ecr'if m[1]=='emr'else spec[0];row.update(tipo=typ,numero=number(m[2]),numero_literal_path=m[2],data=m[3],origem_chave='Padrão canônico explícito de diretório, prefixo, número/sufixo e data');indexed.append(row);count[directory]['reconhecidos_por_filename']+=1
 else:fallback.append(row);count[directory]['metadados_por_OID_obrigatorios']+=1
proc=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
def feed():
 for row in fallback:proc.stdin.write((row['OID']+'\n').encode())
 proc.stdin.close()
t=threading.Thread(target=feed);t.start();held=[];proofs=[]
for i,row in enumerate(fallback,1):
 h=proc.stdout.readline().split();assert len(h)==3 and h[0].decode()==row['OID']and h[1]==b'blob';raw=proc.stdout.read(int(h[2]));assert proc.stdout.read(1)==b'\n';row['sha256_MD_HEAD']=sha(raw);meta={};header=None
 if raw.startswith(b'---\n')and b'\n---\n'in raw[4:]:
  header=raw[4:].split(b'\n---\n',1)[0].decode()
  for line in header.splitlines():
   k,sep,v=line.partition(':')
   if sep:
    v=v.strip()
    try:meta[k]=json.loads(v)
    except ValueError:meta[k]=v
 row['meta_LITERAL']=meta;typ=types.get(n(meta.get('tipo','')));num=number(meta.get('numero',''));date=meta.get('data');proofs.append({'path':row['path'],'OID':row['OID'],'sha256_MD_HEAD':sha(raw),'bytes_MD_HEAD':len(raw),'cabecalho_UTF8_completo':header,'metadata':meta});row['URN_literal']=meta.get('urn');row['fonte_literal']=meta.get('fonte')
 if typ and num and re.fullmatch(r'\d{4}-\d\d-\d\d',str(date or'')):
  row.update(tipo=typ,numero=num,data=date,origem_chave='Metadados completos do blob HEAD por OID, fora do padrão de filename');indexed.append(row);count[row['diretorio']]['chaves_por_metadata_OID']+=1
 else:
  row['motivo_reserva']='Sem chave tipo/série explícita + número literal/sufixo + data. SN e tipos institucionais não são fundidos por semelhança; URN/URL literais preservadas para confronto específico.';held.append(row);count[row['diretorio']]['sem_chave_reservados']+=1
 if i%500==0:print('Metadados por OID',i,flush=True)
t.join();assert proc.wait()==0
assert sum(c['MD_canonicos']for c in count.values())==len(indexed)+len(held);result={'HEAD':head,'tree_gzip':{'path':str(tp.relative_to(R)),'sha256':sha(tp.read_bytes())},'cobertura_por_diretorio':dict(count),'MD_canonicos':sum(c['MD_canonicos']for c in count.values()),'chaves_comparaveis':len(indexed),'fora_padrao_filename_lidos_por_OID':len(fallback),'reservados_sem_chave':len(held),'registros':indexed,'reservas':held,'artefatos_MD_nao_canonicos_excluidos':ignored,'tipos_explicitamente_comparaveis':types,'limites':'Número mantém sufixos alfabéticos/números de reedição; datas e séries distintas não são fundidas. Resoluções exigem tipo institucional explícito; resolução regulatória genérica não é série legislativa. SN/atos sem chave permanecem reservados por caminho/OID, com URN/URL do cabeçalho quando disponíveis. Nenhuma escrita Git/canônica ou máscara.'};(D/'indice_transversal_v2.json.gz').write_bytes(gzip.compress(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode(),mtime=0));(D/'metadados_fallback_OID.jsonl.gz').write_bytes(gzip.compress(('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))for x in proofs)+'\n').encode(),mtime=0));thin={k:v for k,v in result.items()if k not in {'registros','reservas','artefatos_MD_nao_canonicos_excluidos'}};(D/'cobertura_indice_v2.json').write_text(json.dumps(thin,ensure_ascii=False,indent=2)+'\n');print(json.dumps(thin,ensure_ascii=False),flush=True)

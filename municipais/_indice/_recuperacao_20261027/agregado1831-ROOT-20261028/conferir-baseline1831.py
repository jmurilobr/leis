from pathlib import Path
import json,gzip,subprocess,re,hashlib
sha=lambda b:hashlib.sha256(b).hexdigest()
B=Path('municipais/_indice/_recuperacao_20261027/agregado1831-v7-20261028/baseline-com-reservas47/manifesto.json');m=json.loads(B.read_bytes());rows={r['path']:r for r in map(json.loads,gzip.open(m['metadados'],'rt'))};assert len(rows)==34373
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(); raw=subprocess.check_output(['git','ls-tree','-r','-z',head,'--','municipais']); actual={}
for rec in raw.split(b'\0'):
 if not rec:continue
 meta,p=rec.split(b'\t',1);path=p.decode()
 if re.fullmatch(r'municipais/[A-Z]{2}/[^/]+/[^/]+/[^/]+/[^/]+\.md',path):
  mode,typ,oid=meta.split();assert mode==b'100644' and typ==b'blob';actual[path]=oid.decode()
assert set(actual)==set(rows),(len(actual),len(rows)); same=0;read={};proc=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
for path,r in rows.items():
 if r.get('origem')=='HEAD' and r.get('oid')==actual[path]:same+=1;continue
 proc.stdin.write((actual[path]+'\n').encode());proc.stdin.flush();hdr=proc.stdout.readline().split();assert hdr[0].decode()==actual[path] and hdr[1]==b'blob';data=proc.stdout.read(int(hdr[2]));assert proc.stdout.read(1)==b'\n';assert sha(data)==r['sha256'],path;read[path]={'oid':actual[path],'sha256':sha(data)}
proc.stdin.close();assert proc.wait()==0;assert same==32407 and len(read)==1966,(same,len(read));assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==head
out={'HEAD':head,'baseline':str(B),'sha256_baseline':sha(B.read_bytes()),'total':len(actual),'blobs_identicos_por_oid':same,'reservas_agora_publicadas_conferidas_por_sha':read,'criterio':'O conjunto integral do HEAD municipal coincide com o baseline usado na dedup de 1.831 candidatos; as 1.966 reservas foram publicadas exatamente nos SHA esperados. Nenhuma modificação ou remoção adicional.'};p=Path('_fonte/operacao_root_20261027/municipal1831-baseline-atual-root.json');assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(same,len(read),'baseline reconciliado com HEAD')

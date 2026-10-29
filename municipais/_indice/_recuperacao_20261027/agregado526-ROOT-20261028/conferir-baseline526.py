from pathlib import Path
import json,gzip,hashlib,subprocess,re
sha=lambda b:hashlib.sha256(b).hexdigest();B=Path('municipais/_indice/_recuperacao_20261027/agregado526-v7-20261028/baseline-com-reservas47/manifesto.json');m=json.loads(B.read_bytes());rows={r['path']:r for r in map(json.loads,gzip.open(m['metadados'],'rt'))};assert len(rows)==37655
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();tree=subprocess.check_output(['git','ls-tree','-rz',head,'--','municipais']);actual={}
for record in tree.split(b'\0'):
 if not record:continue
 d,p=record.split(b'\t',1);path=p.decode()
 if re.fullmatch(r'municipais/[A-Z]{2}/[^/]+/[^/]+/[^/]+/[^/]+\.md',path):mode,typ,oid=d.split();assert mode==b'100644' and typ==b'blob';actual[path]=oid.decode()
assert set(actual)==set(rows),(len(actual),len(rows));proc=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE);origins={}
for path,r in rows.items():
 proc.stdin.write((actual[path]+'\n').encode());proc.stdin.flush();h=proc.stdout.readline().split();assert h[0].decode()==actual[path] and h[1]==b'blob';raw=proc.stdout.read(int(h[2]));assert proc.stdout.read(1)==b'\n' and sha(raw)==r['sha256'] and len(raw)==r['bytes'];assert raw[4:].split(b'\n---\n',1)[0].decode()==r['cabecalho_integral'];origins[r['origem']]=origins.get(r['origem'],0)+1
 if r['origem']=='HEAD':assert r['oid']==actual[path]
proc.stdin.close();assert proc.wait()==0;assert head==subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();out={'HEAD':head,'baseline':str(B),'sha256_baseline':sha(B.read_bytes()),'MD_canonicos':len(rows),'blobs_integrais_OID_SHA_tamanho_cabecalho':len(rows),'origens_historicas':origins,'reservas_agora_no_HEAD':1010,'reservas_restantes':0,'criterio':'Conjunto canônico exato de HEAD; todos os blobs lidos integralmente por OID. Reserva1010 reconciliada ao conteúdo publicado byte idêntico, sem modificar baseline histórico.'};p=Path('_fonte/operacao_root_20261027/municipal526-baseline-atual-root.json');assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(out)

from pathlib import Path
import json,gzip,hashlib,subprocess,re
sha=lambda b:hashlib.sha256(b).hexdigest();B=Path('municipais/_indice/_recuperacao_20261027/baseline-head-novos-apos36293-20261028/manifesto.json');assert sha(B.read_bytes())=='dd081032d784134d1915b511bf1f2b5d036b86d17d43a2b518c1872b7b69712e';m=json.loads(B.read_bytes());assert m['normas_head']==m['total']==36293 and not m['reservas'];head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();subprocess.run(['git','diff','--quiet',m['commit'],head,'--','municipais'],check=True)
rows={r['path']:r for r in map(json.loads,gzip.open(m['metadados'],'rt'))};assert len(rows)==36293;t=subprocess.check_output(['git','ls-tree','-r','-z',head,'--','municipais']);actual={}
for record in t.split(b'\0'):
 if not record:continue
 d,p=record.split(b'\t',1);path=p.decode()
 if re.fullmatch(r'municipais/[A-Z]{2}/[^/]+/[^/]+/[^/]+/[^/]+\.md',path):mode,typ,oid=d.split();assert typ==b'blob' and mode==b'100644';actual[path]=oid.decode()
assert set(rows)==set(actual);proc=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
for p,r in rows.items():
 assert r['origem']=='HEAD' and r['oid']==actual[p];proc.stdin.write((r['oid']+'\n').encode());proc.stdin.flush();h=proc.stdout.readline().split();assert h[0].decode()==r['oid'] and h[1]==b'blob';raw=proc.stdout.read(int(h[2]));assert proc.stdout.read(1)==b'\n' and len(raw)==r['bytes'] and sha(raw)==r['sha256'];assert raw[4:].split(b'\n---\n',1)[0].decode()==r['cabecalho_integral'],p
proc.stdin.close();assert proc.wait()==0;assert head==subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();out={'HEAD':head,'HEAD_baseline':m['commit'],'baseline':str(B),'sha256_baseline':sha(B.read_bytes()),'MD_canonicos':36293,'blobs_lidos_integralmente_por_OID':36293,'SHA_tamanho_cabecalhos_integrais_conferidos':36293,'reservas_adicionadas':0,'criterio':'ROOT verificou conjunto exato dos canônicos HEAD e leu todos os blobs municipais para conferir OID, SHA, tamanho e cabeçalho integral do baseline usado na dedup. Nenhum delta municipal desde o baseline; sem substituir por versões em disco.'};q=Path('_fonte/operacao_root_20261027/municipal352-baseline-atual-root.json');assert not q.exists();q.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(out)

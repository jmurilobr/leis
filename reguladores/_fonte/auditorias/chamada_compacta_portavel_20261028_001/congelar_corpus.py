"""Corpos e hashes do delta inteiro; fonte positiva segue na prova anterior."""
from pathlib import Path
import json,gzip,hashlib
B=Path(__file__).resolve().parent;R=B.parents[3];sha=lambda b:hashlib.sha256(b).hexdigest();F=R/'reguladores/_fonte/auditorias/dou2017_federal_20261028_001';input_raw=(F/'candidatos2017.json').read_bytes();inputs=json.loads(input_raw)[10000:18000];assert len(inputs)==8000;parts=[];maps=[];stream=None;size=count=idx=0;partpath=None
for i,path in enumerate(inputs):
 raw=(R/path).read_bytes();payload=(json.dumps({'indice':10000+i,'path':path,'sha256_MD':sha(raw),'MD_UTF8':raw.decode()},ensure_ascii=False,separators=(',',':'))+'\n').encode();member=gzip.compress(payload,mtime=0)
 if stream is None or size+len(member)>40*1024**2:
  if stream:stream.close();parts.append({'path':str(partpath.relative_to(R)),'sha256_gzip':sha(partpath.read_bytes()),'bytes_gzip':size,'registros':count})
  idx+=1;partpath=B/f'corpus8000-parte{idx:03}.jsonl.gz';stream=partpath.open('xb');size=count=0
 maps.append({'indice':10000+i,'path':path,'sha256_MD':sha(raw),'bytes_MD':len(raw),'arquivo':str(partpath.relative_to(R)),'offset_gzip':size,'bytes_member':len(member),'sha256_member':sha(member)});stream.write(member);size+=len(member);count+=1
 if (i+1)%1000==0:print(i+1,flush=True)
if stream:stream.close();parts.append({'path':str(partpath.relative_to(R)),'sha256_gzip':sha(partpath.read_bytes()),'bytes_gzip':size,'registros':count})
assert all(p['bytes_gzip']<95*1024**2 for p in parts);m={'entrada':8000,'faixa':[10000,18000],'sha256_inventario_24542':sha(input_raw),'partes':parts,'registros':maps,'gate':{'path':'reguladores/_fonte/auditorias/chamada_compacta_20261028_001/gate_chamada_compacta.py','sha256':'dab2cf45c4b2b9263be4fd6a8a0c29235c2b99d6bfab0c9a95be1ecc745a8937'},'limites':'Corpos Markdown preexistentes integrais para repetir delta lexical, sem presumir autoria. Provas primárias HTML/MD dos dois alertas e controle prospectivo permanecem no overlay anterior. Não qualifica retidos nem afirma revisão humana universal.'};(B/'manifesto8000.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(parts,flush=True)

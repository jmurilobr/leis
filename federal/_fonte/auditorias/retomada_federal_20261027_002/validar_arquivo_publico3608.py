from pathlib import Path
import json,gzip,hashlib
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[3];sha=lambda b:hashlib.sha256(b).hexdigest();mp=BASE/'fontes3608/mapa_fontes3608.json';m=json.loads(mp.read_text());idx={r['path']:r for r in m['registros']};seen=set();pre=0;outputs=[]
for part in m['partes']:
 p=ROOT/part['path'];assert p.stat().st_size==part['bytes_gzip']<95*1024**2 and sha(p.read_bytes())==part['sha256_gzip'];count=0
 with gzip.open(p,'rb') as stream:
  for line in stream:
   obj=json.loads(line);r=idx[obj['path']];assert obj['path'] not in seen and sha(line)==r['sha256_registro_jsonl'];seen.add(obj['path']);assert r['arquivo']==part['path']
   for k,h in [('html_original','sha256_html'),('metadados_raw','sha256_metadados'),('md_final','sha256_md_final')]:assert sha(obj[k].encode())==obj[h]==r[h]
   meta=json.loads(obj['metadados_raw']);assert meta['legislationIdentifier']==obj['urn'] and meta['legislationDate']==obj['data']
   if obj['md_preimagem'] is not None:assert sha(obj['md_preimagem'].encode())==obj['sha256_preimagem']==r['sha256_preimagem'];pre+=1
   count+=1
 with p.open('rb') as compressed:
  pos=0
  for r in [r for r in m['registros'] if r['arquivo']==part['path']]:
   assert r['offset_gzip']==pos;member=compressed.read(r['bytes_gzip_member']);assert sha(member)==r['sha256_member_gzip'] and sha(gzip.decompress(member))==r['sha256_registro_jsonl'];pos+=len(member)
  assert pos==p.stat().st_size
 assert count==part['registros'];outputs.append(dict(part,registros_relidos=count,crc_gzip_integral=True,offsets_members_conferidos=True))
assert len(seen)==3608 and pre==116
res={'escopo':'Releitura independente de todos os bytes do arquivo público preparado; gzip concatenado/CRC, JSONL, hashes de HTML/API/MD/preimagem e offsets exatos de cada membro. Não executa runner de promoção.','resumo':{'registros':len(seen),'preimagens':pre,'partes':len(outputs),'divergencias':0},'partes':outputs};p=BASE/'validacao_arquivo_publico3608.json';assert not p.exists();p.write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n');print(res['resumo'])

from pathlib import Path
import json,gzip,hashlib
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[3];sha=lambda b:hashlib.sha256(b).hexdigest();records=[];prom=[];seen=set();urns=set();allfiles={}
for no in [20,21]:
 manifest=ROOT/f'federal/_lote_dec_continuacao_20261020_{no:03}_v3.json';m=json.loads(manifest.read_text());hp=BASE/f'publicar{no:03}-v3-hashes.json';h=json.loads(hp.read_text())
 for a in h['arquivos']:
  raw=(ROOT/a['path']).read_bytes();assert sha(raw)==a['sha256'];allfiles[a['path']]=a
 for r in m['publicaveis']:
  p=r['path'];assert p not in seen and r['urn'] not in urns;seen.add(p);urns.add(r['urn']);final=r.get('candidato_promocao',p);raw=(ROOT/final).read_bytes();assert sha(raw)==r['sha256'];sp=p.replace('federal/decretos/','federal/_fonte/decretos/').replace('.md','.html.gz');html=gzip.decompress((ROOT/sp).read_bytes());assert sha(html)==r['sha256_fonte_html'];api=gzip.decompress((ROOT/r['captura_metadados']).read_bytes());assert sha(api)==r['sha256_metadados'];obj=json.loads(api);assert obj['legislationIdentifier']==r['urn'] and obj['legislationDate']==r['epigrafe']['data'];original=(ROOT/p).read_bytes()
  if final!=p:assert sha(original)==r['sha256_preimagem'];prom.append({'path':p,'candidate':final,'sha256_preimagem':sha(original),'sha256_candidato':sha(raw)})
  else:assert sha(original)==r['sha256']
  records.append({'path':p,'lote':no,'arquivo_final':final,'urn':r['urn'],'numero':r['epigrafe']['numero'],'data':r['epigrafe']['data'],'sha256_md_final':sha(raw),'sha256_md_canonico':sha(original),'sha256_html':sha(html),'fonte_html_cache':sp,'sha256_metadados':sha(api),'captura_metadados':r['captura_metadados']})
assert len(records)==3608 and len(prom)==116
for name,obj in [('verificacao_3608.json',{'resumo':{'normas':3608,'promocoes':116,'divergencias':0},'registros':records}),('promocoes_116.json',{'substituicoes':prom}),('publicar3608-hashes.json',{'arquivos':sorted(allfiles.values(),key=lambda a:a['path'])})]:
 p=BASE/name;assert not p.exists();p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
(BASE/'publicar3608-paths.txt').write_text('\n'.join(sorted(allfiles))+'\n');print('normas',len(records),'promocoes',len(prom),'arquivos',len(allfiles))

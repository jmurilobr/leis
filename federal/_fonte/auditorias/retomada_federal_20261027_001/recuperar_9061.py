import sys,json,hashlib,gzip,subprocess,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from preparar_lote_decretos_cache import fields
from identidade_decreto import numero_normalizado
BASE=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();assert head=='15eb09b618ff08a38c4dfee06a91bd139d093f5d'
files={};errors=[];records=[];promotions=[];paths=set();urns=set();keys=set();manifestos=[]
def check(path,expected=None,kind='prova'):
 p=ROOT/path
 try:raw=p.read_bytes();h=sha(raw)
 except Exception as e:errors.append({'path':path,'erro':str(e)});return None
 if expected and h!=expected:errors.append({'path':path,'esperado':expected,'encontrado':h,'tipo':kind})
 if path in files:assert files[path]['sha256']==h
 files[path]={'path':path,'sha256':h,'bytes':len(raw),'tipo':kind};return raw
for no,ver in [(15,4),(16,4),(17,4),(18,4),(19,3)]:
 mp=f'federal/_lote_dec_continuacao_20261020_{no:03}_v{ver}.json';raw=check(mp);m=json.loads(raw);manifestos.append({'path':mp,'sha256':sha(raw),'resumo':m['resumo']})
 for proof in m['provas']:check(proof['path'],proof['sha256'])
 if m.get('manifesto_anterior'):check(m['manifesto_anterior']['path'],m['manifesto_anterior']['sha256'])
 for r in m['publicaveis']:
  p=r['path'];assert p not in paths and r['urn'] not in urns;paths.add(p);urns.add(r['urn']);ep=r['epigrafe'];key=(numero_normalizado(ep['numero']),ep['data'][:4]);assert key not in keys;keys.add(key)
  final=r.get('candidato_promocao',p);body=check(final,r['sha256'],'MD_final');meta,_,_=fields(body.decode());assert meta['urn']==r['urn'] and meta['data']==ep['data'] and numero_normalizado(meta['numero'])==key[0]
  original=(ROOT/p).read_bytes();h=sha(original);state='canônico igual ao final'
  if final!=p:
   expected=r['sha256_preimagem'];assert h in {expected,r['sha256']},(p,h,expected);state='preimagem canônica intacta' if h==expected else 'canônico já promovido por ROOT';promotions.append({'path':p,'candidate':final,'sha256_preimagem':expected,'sha256_candidato':r['sha256'],'sha256_canonico_observado':h,'estado':state})
  else:assert h==r['sha256']
  source=p.replace('federal/decretos/','federal/_fonte/decretos/').replace('.md','.html.gz');src=gzip.decompress((ROOT/source).read_bytes());assert sha(src)==r['sha256_fonte_html'],p
  api=gzip.decompress((ROOT/r['captura_metadados']).read_bytes());assert sha(api)==r['sha256_metadados'];apiobj=json.loads(api);assert apiobj['legislationIdentifier']==r['urn'] and apiobj['legislationDate']==ep['data'];assert apiobj['legislationType'] in {'Decreto Numerado','Decreto'}
  records.append({'path':p,'lote':no,'arquivo_final':final,'urn':r['urn'],'numero':key[0],'data':ep['data'],'sha256_md_final':sha(body),'sha256_md_canonico':h,'sha256_html':sha(src),'fonte_html_cache':source,'sha256_metadados':sha(api),'captura_metadados':r['captura_metadados'],'estado':state})
 print('recuperado',no,len(m['publicaveis']),'total',len(records),flush=True)
assert len(records)==9061 and len(promotions)==395
# Query only these exact HEAD paths; no index access or mutation.
q=subprocess.run(['git','cat-file','--batch-check'],cwd=ROOT,input=''.join('HEAD:'+r['path']+'\n' for r in records),text=True,capture_output=True,check=True);lines=q.stdout.splitlines();assert len(lines)==9061
headpresent=[]
for r,line in zip(records,lines):
 if not line.endswith(' missing'):headpresent.append({'path':r['path'],'resultado':line})
summary={'HEAD':head,'manifestos':manifestos,'resumo':{'normas':len(records),'promocoes':len(promotions),'provas_e_MD_hash_verificados':len(files),'divergencias':len(errors),'destinos_presentes_HEAD':len(headpresent),'estados_promocao':dict(collections.Counter(r['estado'] for r in promotions))},'divergencias':errors,'destinos_presentes_HEAD':headpresent,'registros':records}
assert not errors,errors[:3]
for name,obj in [('verificacao_9061.json',summary),('promocoes_395.json',{'escopo':'Mapa reconstruído dos candidatos e preimagens, sem promover ou alterar os arquivos.','substituicoes':promotions}),('hashes_arquivos.json',{'arquivos':sorted(files.values(),key=lambda r:r['path'])})]:
 p=BASE/name;assert not p.exists();p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
(BASE/'publicar-paths.txt').write_text('\n'.join(sorted(files))+'\n');print(summary['resumo'],flush=True)

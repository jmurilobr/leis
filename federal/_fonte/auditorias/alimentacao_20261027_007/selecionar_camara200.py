from pathlib import Path
import json,hashlib,gzip,subprocess,re
B=Path(__file__).resolve().parent;R=B.parents[3];sha=lambda b:hashlib.sha256(b).hexdigest();head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();tree=subprocess.check_output(['git','ls-tree','-rz','--name-only',head,'--','federal/decretos'],cwd=R);ids=set()
for p in tree.decode().split('\0'):
 m=re.search(r'federal/decretos/(\d{4})/dec-(.+)-\d{4}-\d\d-\d\d.md$',p)
 if m:ids.add((m[2],m[1]))
excluded=set();inputs=[]
for name in ['005','006']:
 p=R/f'federal/_fonte/auditorias/alimentacao_20261027_{name}/fila_camara100.json';raw=p.read_bytes();inputs.append({'path':str(p.relative_to(R)),'sha256':sha(raw)});excluded.update(x['path'] for x in json.loads(raw)['candidatos'])
q=[]
for no in [24,23,22]:
 C=R/f'federal/_fonte/auditorias/lote_dec_continuacao_20261020_{no:03}';cp=C/'coleta.json';raw=cp.read_bytes();inputs.append({'path':str(cp.relative_to(R)),'sha256':sha(raw)})
 for x in json.loads(raw)['registros']:
  d=x.get('detalhe',{});n=str(x['indice']['numero']);y=str(x['indice']['anoassinatura'])
  if x['path'] in excluded or x['status']!='sem_texto' or not isinstance(d,dict) or d.get('motivo') or 'url' in d or n in {'6218','6220'} or (n,y) in ids:continue
  u=d['urn'];files=list((C/'work/_fonte/metadados-normas'/sha(u.encode())).glob('*.json.gz'));assert len(files)==1;mr=gzip.decompress(files[0].read_bytes());meta=json.loads(mr);assert meta['legislationIdentifier']==u
  if meta.get('encoding'):continue
  assert not (R/x['path']).exists(),x['path'];excluded.add(x['path']);q.append({**x,'metadados_preexistentes':str(files[0].relative_to(R)),'sha256_metadados_raw':sha(mr),'encoding_vazio_confirmado':True})
  if len(q)==200:break
 if len(q)==200:break
assert len(q)==200;out={'HEAD':head,'guard_sha256':sha((R/'scripts/integridade_anexos_decreto.py').read_bytes()),'insumos_snapshot':inputs,'candidatos':q,'escopo':'Duzentas identidades oficiais sem encoding, ausentes em HEAD/disco. Excluídos os dois lotes anteriores e os pilotos; nenhum HTTP nesta seleção. Câmara como fonte alternativa, sem repetir capturas Normas vazias.'};p=B/'fila_camara200.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('Fila200',q[0]['path'],q[-1]['path'])

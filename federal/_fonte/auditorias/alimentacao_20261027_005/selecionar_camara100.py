from pathlib import Path
import json,hashlib,gzip,subprocess,re
B=Path(__file__).resolve().parent;R=B.parents[3];sha=lambda b:hashlib.sha256(b).hexdigest();C=R/'federal/_fonte/auditorias/lote_dec_continuacao_20261020_024';rows=json.loads((C/'coleta.json').read_bytes())['registros'];head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();tree=subprocess.check_output(['git','ls-tree','-rz','--name-only',head,'--','federal/decretos'],cwd=R);ids=set()
for p in tree.decode().split('\0'):
 m=re.search(r'federal/decretos/(\d{4})/dec-(.+)-\d{4}-\d\d-\d\d.md$',p)
 if m:ids.add((m[2],m[1]))
q=[]
for x in rows:
 d=x.get('detalhe',{});n=str(x['indice']['numero']);y=str(x['indice']['anoassinatura'])
 if x['status']!='sem_texto' or not isinstance(d,dict) or d.get('motivo') or 'url' in d or n in {'6218','6220'} or (n,y) in ids:continue
 u=d['urn'];files=list((C/'work/_fonte/metadados-normas'/sha(u.encode())).glob('*.json.gz'));assert len(files)==1;raw=gzip.decompress(files[0].read_bytes());meta=json.loads(raw);assert meta['legislationIdentifier']==u
 if meta.get('encoding'):continue
 assert not (R/x['path']).exists(),x['path'];q.append({**x,'metadados_preexistentes':str(files[0].relative_to(R)),'sha256_metadados_raw':sha(raw),'encoding_vazio_confirmado':True})
 if len(q)==100:break
assert len(q)==100;out={'HEAD':head,'guard_sha256':sha((R/'scripts/integridade_anexos_decreto.py').read_bytes()),'candidatos':q,'escopo':'Cem metadados oficiais preexistentes sem encoding, ausentes por número/ano em HEAD e por caminho no disco; excluídos pilotos anteriores. Câmara como alternativa legítima, sem repetir Normas. Nenhuma identidade ou íntegra presumida por busca.'};p=B/'fila_camara100.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('Fila',len(q),q[0]['path'],q[-1]['path'])

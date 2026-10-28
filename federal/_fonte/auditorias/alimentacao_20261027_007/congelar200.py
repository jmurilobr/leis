from pathlib import Path
import json,gzip,hashlib,subprocess,re,base64
B=Path(__file__).resolve().parent;ROOT=B.parents[3];sha=lambda x:hashlib.sha256(x).hexdigest();q=json.loads((B/'fila_camara200.json').read_bytes());prep=json.loads((B/'preparo200_v2.json').read_bytes());qa=json.loads((B/'replay200_v2.json').read_bytes());approved={r['path']:r for r in qa['registros'] if r['aprovado']};rows=[r for r in prep['registros'] if r['path'] in approved];head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();tree=subprocess.check_output(['git','ls-tree','-rz','--name-only',head,'--','federal/decretos'],cwd=ROOT);known=set()
for p in tree.decode().split('\0'):
 m=re.search(r'federal/decretos/(\d{4})/dec-(.+)-\d{4}-\d\d-\d\d.md$',p)
 if m:known.add((m[2],m[1]))
paths=set();urns=set();ids=set();plan=[];proofs=[]
for c in q['candidatos']:
 path=c['path'];pr=json.loads((B/(str(c['indice']['numero'])+'-resultado.json')).read_bytes());metaraw=gzip.decompress((ROOT/c['metadados_preexistentes']).read_bytes());assert sha(metaraw)==c['sha256_metadados_raw'];sources=[]
 for k in ['busca','pagina_norma','texto_original']:
  if k in pr:
   r=pr[k];raw=gzip.decompress((ROOT/r['arquivo']).read_bytes());assert sha(raw)==r['sha256_raw'];sources.append({'papel':k,'recibo':r,'bytes_originais_base64':base64.b64encode(raw).decode()})
 row=next((r for r in rows if r['path']==path),None);out={'fila':c,'coleta':pr,'metadados_raw':metaraw.decode(),'fontes_completas':sources,'candidato_aprovado':row,'replay':approved.get(path)}
 if row:
  raw=(ROOT/row['candidato']).read_bytes();assert sha(raw)==row['sha256_candidato'];assert not (ROOT/path).exists();identity=(str(row['indice_senado']['numero']),row['indice_senado']['anoassinatura']);assert identity not in known and identity not in ids and path not in paths and row['urn'] not in urns;paths.add(path);urns.add(row['urn']);ids.add(identity);out['md_final_utf8']=raw.decode();plan.append({'path':path,'candidato':row['candidato'],'sha256_final':sha(raw),'preimagem':'ausente no disco e no HEAD conferido','urn':row['urn'],'numero':identity[0],'ano':identity[1]})
 proofs.append(out)
archive=B/'fontes_e_provas200.jsonl.gz';assert not archive.exists();archive.write_bytes(gzip.compress(('\n'.join(json.dumps(x,ensure_ascii=False) for x in proofs)+'\n').encode(),mtime=0));assert archive.stat().st_size<95*1024**2
# Reabre e reconfere todos os registros e bytes originais, inclusive falhas de catálogo.
reread=[json.loads(x) for x in gzip.decompress(archive.read_bytes()).splitlines()];assert len(reread)==200
for x in reread:
 assert sha(x['metadados_raw'].encode())==x['fila']['sha256_metadados_raw']
 for source in x['fontes_completas']:assert sha(base64.b64decode(source['bytes_originais_base64']))==source['recibo']['sha256_raw']
 if x['candidato_aprovado']:assert sha(x['md_final_utf8'].encode())==x['candidato_aprovado']['sha256_candidato']
m={'escopo':'Primeiro lote Câmara 200 alternativo para metadados Normas históricos sem encoding; somente candidatos privados, sem escrever destinos canônicos.','HEAD_dedup':head,'guard_sha256':q['guard_sha256'],'resumo':qa['resumo'],'publicaveis_privados':rows,'plano_novas_inclusoes_ROOT':plan,'retidos_preparo':prep['retidos'],'retidos_replay':[r for r in qa['registros'] if not r['aprovado']],'fontes_e_provas':{'path':str(archive.relative_to(ROOT)),'sha256':sha(archive.read_bytes()),'bytes_gzip':archive.stat().st_size,'registros':200,'releitura_integral_sha_CRC_aprovada':True},'limites':qa['limites']+' Não certifica vigência. Os casos sem link de Original não são declarados inexistentes. Todas as capturas e resultados anteriores foram preservados. ROOT revisa e promove novas inclusões.'};mp=B/'lote_camara200.json';assert not mp.exists();mp.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');files=[Path(__file__),B/'replay_portavel200.py',B/'selecionar_camara200.py',B/'coletar_camara200.py',B/'preparar_QA200_v2.py',B/'fila_camara200.json',B/'checkpoint_coleta.json',B/'coleta.log',B/'preparo200_v2.json',B/'replay200_v2.json',B/'render200_input_v2.json',B/'render200_marked_v2.json',mp,archive,ROOT/'federal/_fonte/auditorias/retomada_federal_20261027_003/render_estrutural_v2.mjs']+[ROOT/r['candidato'] for r in rows];lp=B/'entrega-camara200-paths.txt';lp.write_text('\n'.join(str(p.relative_to(ROOT)) for p in files)+'\n');(B/'entrega-camara200-hashes.json').write_text(json.dumps({'sha256_lista':sha(lp.read_bytes()),'arquivos':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes())} for p in files]},indent=2)+'\n');print('Congelado',len(rows),'candidatos,',len(files),'arquivos, fontes',archive.stat().st_size,'bytes',flush=True)

from pathlib import Path
import json,gzip,hashlib,os,time,subprocess,sys
B=Path(__file__).resolve().parent;R=B.parents[3];pid=78186
while True:
 try:os.kill(pid,0)
 except ProcessLookupError:break
 time.sleep(5)
cp=json.loads((B/'checkpoint.json').read_bytes());assert cp['resumo']['concluidos']==2000 and not cp['resumo']['recusa'];n=0
for p in (B/'requests').glob('*.json'):
 x=json.loads(p.read_bytes())
 if x.get('status_http')!=200:continue
 raw=gzip.decompress((R/x['arquivo_raw']).read_bytes());assert hashlib.sha256(raw).hexdigest()==x['sha256_raw'];n+=1
proof={'resumo':cp['resumo'],'recibos_HTTP_200_CRC_SHA_conferidos':n,'guard_sha256':cp['snapshot']['guard_sha256'],'PID_anterior':pid,'termino_confirmado':True,'limites':'Integridade de captura, não certificação de íntegra normativa; nenhum canônico alterado.'};(B/'validacao_checkpoint_final.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');print(proof,flush=True)
steps=[['qualificar_snapshot_v4.py','--nome','qa_final_v4'],['replay_HTML5_snapshot.py','--qa','qa_final_v4','--saida','html5_final001'],['reparar_render_nativo_snapshot.py','--qa','qa_final_v4','--saida','reparos_nativos_final001'],['testar_limites_v4.py'],['inventariar_vinculos_tecnicos.py']]
for args in steps:
 print('Executando',args,flush=True);subprocess.run([sys.executable,str(B/args[0])]+args[1:],cwd=R,check=True)

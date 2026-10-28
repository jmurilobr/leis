from pathlib import Path
import json,gzip,hashlib,sys,types,subprocess
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[3];sys.path.insert(0,str(ROOT/'scripts'));from preparar_lote_decretos_cache import fields
from integridade_html_federal import Visivel
import integridade_anexos_decreto as guard56
sha=lambda b:hashlib.sha256(b).hexdigest();oldraw=subprocess.check_output(['git','show','9f40d93db2a7b7959c0dda8469cf73c75a3b805b:scripts/integridade_anexos_decreto.py'],cwd=ROOT);expected=json.loads((ROOT/'federal/_proposta_guard_lacunas_20261021_015/recibo.json').read_text())['sha_guard35'];assert sha(oldraw)==expected;g35=types.ModuleType('guard35_snapshot');exec(compile(oldraw.decode(),'guard35-publicado9f40d93','exec'),g35.__dict__);out=[];deltas=[];by=[]
for no in [22,23,24]:
 rows=json.loads((ROOT/f'federal/_lote_dec_continuacao_20261020_{no:03}.json').read_text())['publicaveis'];count=0
 for r in rows:
  raw=(ROOT/r['path']).read_bytes();assert sha(raw)==r['sha256'];body=fields(raw.decode())[2];sp=ROOT/r['path'].replace('federal/decretos/','federal/_fonte/decretos/').replace('.md','.html.gz');src=gzip.decompress(sp.read_bytes());assert sha(src)==r['sha256_fonte_html'];parsed=Visivel();parsed.feed(src.decode());before=g35.anexo_proprio_ausente(body,parsed);after=guard56.anexo_proprio_ausente(body,parsed);rec={'path':r['path'],'lote':no,'sha256_md':sha(raw),'sha256_html':sha(src),'guard35':before,'guard56':after};out.append(rec)
  if before!=after:deltas.append(rec);count+=1
 by.append({'lote':no,'corpos':len(rows),'deltas':count});print(no,len(rows),'deltas',count,flush=True)
res={'escopo':'Delta dos guards35→56 somente nos candidatos inéditos 022–024. Não aplica máscara em HEAD ou qualquer norma publicada.','sha256_guard35':sha(oldraw),'sha256_guard56':sha((ROOT/'scripts/integridade_anexos_decreto.py').read_bytes()),'resumo':{'corpos':len(out),'deltas':len(deltas)},'lotes':by,'registros':out,'deltas':deltas};p=BASE/'replay_delta_guard56_022024.json';assert not p.exists();p.write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')

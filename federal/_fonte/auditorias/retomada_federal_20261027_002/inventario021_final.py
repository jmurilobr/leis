from pathlib import Path
import json,re,sys,unicodedata
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[3];sys.path.insert(0,str(ROOT/'scripts'));from estados.pe_fidelidade_visivel import texto_visivel_html
rows=json.loads((BASE/'preparo021_final.json').read_text())['publicaveis'];render={r['path']:r for r in json.loads((BASE/'render021_final_output.json').read_text())['registros']};out=[]
for r in rows:
 s=texto_visivel_html(render[r['path']]['html']);n=''.join(c for c in unicodedata.normalize('NFD',s) if not unicodedata.combining(c));matches=list(re.finditer(r'(?i)\bilegivel\b|\bdesenhos?\b[^.;]{0,80}?\banex[oa]s?\b',n));arts=list(re.finditer(r'(?i)\bart\.?\s*(?:\d+[º°o]?|unico)',n));oc=[]
 for m in matches:
  before=[a for a in arts if a.start()<=m.start()];after=[a for a in arts if a.start()>m.end()];a=before[-1].start() if before else max(0,m.start()-350);b=after[0].start() if after else len(s);oc.append({'literal':s[m.start():m.end()],'artigo_ou_contexto_integral':s[a:b]})
 if oc:out.append({'path':r['path'],'sha256_md_final':r['sha256'],'sha256_html':r['sha256_fonte_html'],'ocorrencias':oc})
res={'escopo':'Inventário contextual lexical dos corpos finais 021, sem notas YAML; não altera normas ou registro.','resumo':{'corpos_pesquisados':len(rows),'normas_com_ocorrencias':len(out),'ocorrencias':sum(len(r['ocorrencias']) for r in out)},'registros':out,'limites':'Busca lexical não prova integralidade universal ou ausência em outra edição. O caso temporal 12.057/1943 continua retido.'};(BASE/'inventario021_final.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n');print(res['resumo'])

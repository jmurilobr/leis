"""Fecha lotes V7 privados com HEAD real, reservas qualificadas e provas completas.

Só lê Git. Não altera normas existentes: produz controles, exportações isoladas e
um mapa exato de publicação para ROOT. Qualquer gate inconclusivo retém o caso.
"""
from pathlib import Path
import argparse,collections,datetime as dt,gzip,hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'scripts/bin/qa-20261027/python'),str(ROOT/'scripts')]
import promover_reparos_ta47_20261028 as q
from auditar import validar
from auditar_municipal import metadados
from congelar_baseline_municipal_head_20261027 import registro
BASE=q.BASE
FUTURE=BASE/'reparos47-sucessor-v2-20261028/manifesto.json'
FUTURE_SHA='33d0fcd13232666b39bbd5b097cf5629c12762980ef562cfdc9827165b79bb13'

def save(p,value):
 with p.open('x') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def run(script,*args,ok=True):
 result=subprocess.run([sys.executable,'-I',str(ROOT/'scripts'/script),*map(str,args)],cwd=ROOT,text=True,capture_output=True)
 if result.returncode and ok:raise RuntimeError(script+'\n'+result.stdout+'\n'+result.stderr)
 return result

def baseline_futuro(original,output):
 """Reserva futura vem dos candidatos e seus SHAs, nunca do MD antigo no disco."""
 m=json.loads(original.read_text());source=q.safe(m['metadados']);rows=list(map(json.loads,gzip.open(source,'rt')));by={r['path']:r for r in rows}
 frozen=q.verificar_manifesto(FUTURE,FUTURE_SHA);candidates=json.loads(q.safe(frozen['mapa_candidatos']).read_text())['candidatos'];already=[];added=[]
 if len(candidates)!=47 or len({r['path'] for r in candidates})!=47:raise ValueError('Reserva47 ambígua')
 for c in candidates:
  raw=q.safe(c['candidato']).read_bytes()
  if q.sha(raw)!=c['sha256_candidato']:raise ValueError('SHA candidato da reserva mudou')
  if c['path'] in by:
   if by[c['path']]['sha256']!=q.sha(raw):raise ValueError('Reserva47 diverge de HEAD')
   already.append(c['path']);continue
  row=registro(c['path'],None,raw,'reserva futura qualificada por ROOT');row.update(recibo_reserva=str(FUTURE.relative_to(ROOT)),sha256_recibo_reserva=FUTURE_SHA,candidato_sha256=q.sha(raw));rows.append(row);added.append(c['path'])
 output.mkdir(exist_ok=False);target=output/'metadados-integrais.jsonl.gz'
 with gzip.open(target,'wt',encoding='utf-8',compresslevel=1) as f:
  for r in sorted(rows,key=lambda r:r['path']):f.write(json.dumps(r,ensure_ascii=False)+'\n')
 names=output/'normas.paths.txt';names.write_text(''.join(r['path']+'\n' for r in sorted(rows,key=lambda r:r['path'])))
 records={r['arquivo']:r for r in m['arquivos']}
 for p in [original,FUTURE,q.safe(frozen['mapa_candidatos']),target,names,Path(__file__).resolve()]:records[str(p.relative_to(ROOT))]=q.info(p)
 for c in candidates:
  p=q.safe(c['candidato']);records[str(p.relative_to(ROOT))]=q.info(p)
 m.update(total=len(rows),metadados=str(target.relative_to(ROOT)),arquivos=list(records.values()),reservas=m['reservas']+[dict(recibo=str(FUTURE.relative_to(ROOT)),sha256=FUTURE_SHA,normas=47,ja_no_head=already,adicionadas=len(added))],limite='HEAD integral por OID; reservas explícitas validadas. Os 47 usam o SHA e metadados do candidato futuro, não a preimagem canônica antiga.')
 save(output/'manifesto.json',m);return output/'manifesto.json'

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--saida',type=Path,required=True);ap.add_argument('--componente',nargs=6,action='append',required=True,metavar=('ROTULO','SELECAO','GATES','MATERIALIZADOS','CONTEXTO','COMMONMARK'));a=ap.parse_args();out=a.saida.resolve()
 if not out.is_relative_to(BASE):raise ValueError('Saída fora do controle privado')
 out.mkdir(exist_ok=False);components=[];all_rows={};retained=[];artifacts={}
 def add(p):
  p=Path(p).resolve();r=q.info(p);key=r['arquivo']
  if key in artifacts and artifacts[key]!=r:raise ValueError('Arquivo mudou durante fechamento')
  artifacts[key]=r
 for label,selection,gates,material,context,common in a.componente:
  selection=Path(selection);gates=Path(gates);material=Path(material);context=Path(context);common=Path(common);dest=out/label;dest.mkdir();records={r['path']:r for r in map(json.loads,(material/'resultados.jsonl').read_text().splitlines()) if r['aprovado']}
  selected=set((context/'aprovados.paths.txt').read_text().splitlines())&set((common/'aprovados.paths.txt').read_text().splitlines());pre=dest/'pre-jurisdicao.paths.txt';pre.write_text(''.join(p+'\n' for p in sorted(selected)))
  run('auditar_jurisdicao_ta.py','--lista',pre,'--materializados',material,'--saida',dest/'jurisdicao');names=(dest/'jurisdicao/aprovados.paths.txt').read_text().splitlines();final=[];formats=[]
  for path in names:
   raw=q.safe(path).read_bytes();errors,warnings=validar(raw.decode(),path,dt.date.today())
   formats.append(dict(path=path,sha256=q.sha(raw),erros=errors,avisos=warnings))
   if errors or warnings:retained.append(dict(path=path,gate='formato',erros=errors,avisos=warnings));continue
   if path in all_rows:raise ValueError('Mesmo destino em dois componentes')
   all_rows[path]=dict(records[path],componente=label);final.append(path)
  for path in set(records)-set(final):retained.append(dict(path=path,gate='contexto/CommonMark/jurisdição/formato'))
  save(dest/'formato.json',dict(arquivos=len(formats),problemas=sum(bool(r['erros'] or r['avisos']) for r in formats),resultados=formats))
  components.append(dict(rotulo=label,selecao=str(selection),gates=str(gates),materializados=str(material),contexto=str(context),commonmark=str(common),preliminares=len(final)))
  for folder in [gates,material,context,common]:
   for p in folder.iterdir():
    if p.is_file():add(p)
  add(selection/'snapshot.json')
 # A lista de reservas 921/586 é reconciliada por SHA quando já está em HEAD.
 command=[sys.executable,'-I',str(ROOT/'scripts/congelar_baseline_municipal_head_20261027.py'),'--saida',str(out/'baseline-head')]
 for p,digest in q.RESERVAS:command+=['--reserva',str(BASE/p),digest]
 completed=subprocess.run(command,cwd=ROOT,check=True,text=True,capture_output=True);(out/'baseline-head.log').write_text(completed.stdout+completed.stderr)
 baseline=baseline_futuro(out/'baseline-head/manifesto.json',out/'baseline-com-reservas47')
 listing=out/'preliminares.paths.txt';listing.write_text(''.join(p+'\n' for p in sorted(all_rows)));run('comparar_baseline_municipal_head_20261027.py','--baseline',baseline,'--lista',listing,'--saida',out/'colisoes-preliminares.json',ok=False)
 collision=json.loads((out/'colisoes-preliminares.json').read_text());blocked=set()
 for r in collision['colisoes']:
  blocked.add(r['path']);blocked.update(e['path'] for e in r['existentes'] if e['path'] in all_rows)
 for path in sorted(blocked):retained.append(dict(path=path,gate='colisão HEAD/reserva/candidato',evidencia='colisoes-preliminares.json'));all_rows.pop(path,None)
 names=sorted(all_rows);normlist=out/'normas.paths.txt';normlist.write_text(''.join(p+'\n' for p in names));run('comparar_baseline_municipal_head_20261027.py','--baseline',baseline,'--lista',normlist,'--saida',out/'confronto-final.json')
 for c in components:
  dest=out/c['rotulo'];selected=[p for p in names if all_rows[p]['componente']==c['rotulo']];p=dest/'normas.paths.txt';p.write_text(''.join(n+'\n' for n in selected));c['normas']=len(selected)
  if selected:
   run('verificar_textos_articulados_materializados_v2_privado_20261027.py','--lista',p,'--materializados',c['materializados'],'--saida',dest/'verificacao-integral.json')
   run('auditar_municipal.py','--lista',p,'--saida',dest/'auditoria-municipal.json');audit=json.loads((dest/'auditoria-municipal.json').read_text())
   if audit['problemas'] or audit['avisos']:raise ValueError('Auditoria municipal encontrou pendência')
 mapping=[];export=[];exportdir=out/'exportados';exportdir.mkdir()
 for i,path in enumerate(names):
  r=all_rows[path];raw=q.safe(path).read_bytes()
  if q.sha(raw)!=r['sha256']:raise ValueError('Norma mudou')
  add(ROOT/path);copied=exportdir/(str(i)+'.txt');copied.write_bytes(raw);add(copied);export.append(dict(path=path,exportado=str(copied.relative_to(ROOT)),sha256=q.sha(raw),bytes=len(raw)))
  mapping.append(dict(path=path,sha256=r['sha256'],fonte=r['prova_frontend'],prova_tabelas=r['gates'].get('tabelas_nativas_prova'),**{k:v for k,v in r.items() if k not in {'path','sha256'}}))
  for key in ['prova_frontend','prova_norma','prova_ta','prova_casa']:
   proof=r[key];q.prova_arquivo(proof);p=q.safe(proof['arquivo']);add(p);add(q.safe(proof.get('metadata')) if proof.get('metadata') else p.with_suffix('.meta.json'))
  add(q.safe(r['transcricao']));add(q.safe(r['transcricao_original']))
 for c in components:
  for p in Path(c['gates']).glob('*.anexos.json'):
   for e in json.loads(p.read_text()).get('evidencias',[]):q.prova_arquivo(e);add(q.safe(e['arquivo']));add(q.safe(e['arquivo']).with_suffix('.meta.json'))
 save(out/'mapeamento-fontes.json',mapping);save(out/'exportacao-isolada.json',dict(normas=len(export),arquivos=export,canonicos_alterados=0));save(out/'retencoes.json',dict(resultados=retained,limite='Retenção preventiva; arquivos privados preservados sem promoção por contagem.'))
 code=set((BASE/'lotes/ta-final274-0018/codigo.paths.txt').read_text().splitlines())|{str(p.relative_to(ROOT)) for p in (ROOT/'scripts').glob('*2026102[78].py') if p.name in {'perfil_ta_tachados_preservados_20261027.py','diagnosticar_css_glifos_ta_20261027.py','materializar_textos_articulados_sapl_v7_privado_20261027.py','verificar_textos_articulados_materializados_v2_privado_20261027.py','auditar_commonmark_ta_v3_privado_20261027.py','verificar_entrega_ta_sem_promocoes_v3_privado_20261027.py','promover_reparos_ta47_20261028.py','preparar_reparos_escapes_ta_46_20261027.py','fechar_lotes_municipais_v7_20261028.py'}}
 code|={'scripts/congelar_baseline_municipal_head_20261027.py','scripts/comparar_baseline_municipal_head_20261027.py','federal/_fonte/auditorias/diagnostico_glifos1347_20261027_002/diagnosticar.py'}
 for p in code:add(ROOT/p)
 for p in [ROOT/'municipais/_indice/ibge-municipios.json',FUTURE]:add(p)
 for p in out.rglob('*'):
  if p.is_file():add(p)
 (out/'TESTAR.txt').write_text('Replay integral: Python bundled -I scripts/verificar_entrega_ta_sem_promocoes_v3_privado_20261027.py --manifesto ESTE_DIRETORIO/manifesto.json --replay --saida NOVO_CONTROLE.json\nConferir HEAD atual, fontes/API, mapa de publicação e SHA antes de staging. Datas de captura preservadas, sem inferência de vigência. Não formatar hardbreaks/EOF. Exportação isolada contém cópias .txt byte-identical, sem sobrepor originais.\n');add(out/'TESTAR.txt')
 m=dict(normas=len(names),lista_normas=str(normlist.relative_to(ROOT)),mapeamento_fontes=str((out/'mapeamento-fontes.json').relative_to(ROOT)),componentes=components,baseline=str(baseline.relative_to(ROOT)),confronto=str((out/'confronto-final.json').relative_to(ROOT)),exportacao_isolada=str((out/'exportacao-isolada.json').relative_to(ROOT)),arquivos=sorted(artifacts.values(),key=lambda r:r['arquivo']),limite='Novos candidatos privados qualificados por V7, API/M, identidade, captura real, contexto, replay integral e dedup HEAD+reservas. Fonte histórica retida no bruto; tachados preservados, sem classificação jurídica.')
 receipt=out/'manifesto.json';save(receipt,m);print(json.dumps(dict(normas=len(names),componentes={c['rotulo']:c['normas'] for c in components},manifesto=q.info(receipt))))
if __name__=='__main__':main()

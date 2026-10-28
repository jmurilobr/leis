"""Agrega componentes V7 congelados, com confronto por OID e reservas explícitas."""
from pathlib import Path
import argparse,json,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import promover_reparos_ta47_20261028 as q
from fechar_lotes_municipais_v7_20261028 import baseline_futuro

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--saida',type=Path,required=True);ap.add_argument('--componente',nargs=3,action='append',required=True,metavar=('MANIFESTO','SHA256','NORMAS'));ap.add_argument('--reserva',nargs=2,action='append',default=[]);ap.add_argument('--dependencia',type=Path,action='append',default=[]);a=ap.parse_args();packages=[(str(Path(p).resolve().relative_to(q.BASE)),digest,int(count)) for p,digest,count in a.componente];total=sum(count for _,_,count in packages);out=a.saida.resolve()
 if not out.is_relative_to(q.BASE):raise ValueError('Saída fora do controle privado')
 out.mkdir(exist_ok=False);files={};overlaps=[];mapping=[];exports=[];cssrows=[];replayrows=[];components=[];names=set();cssinputs=[]
 def add(r):
  key=r['arquivo']
  if key in files:
   if files[key]!=r:raise ValueError('Divergência de SHA compartilhado: '+key)
   overlaps.append(key)
  files[key]=r
 def save(name,data):
  p=out/name
  with p.open('x') as f:f.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
  add(q.info(p));return str(p.relative_to(ROOT))
 for path,digest,count in packages:
  p=q.BASE/path;m=q.verificar_manifesto(p,digest)
  if m['normas']!=count:raise ValueError('Cardinalidade do componente mudou')
  for r in m['arquivos']:add(r)
  add(q.info(p));source=json.loads(q.safe(m['manifesto_origem']['arquivo']).read_text());listed=q.safe(m['lista_normas']).read_text().splitlines();mapped=json.loads(q.safe(m['mapeamento_fontes']).read_text())
  if len(listed)!=count or len(set(listed))!=count or names.intersection(listed) or {r['path'] for r in mapped}!=set(listed):raise ValueError('Componentes não disjuntos')
  names.update(listed);mapping+=mapped
  e=json.loads(q.safe(source['exportacao_isolada']).read_text())
  if e['normas']!=count or e['canonicos_alterados']!=0:raise ValueError('Exportação isolada não comprovada')
  for r in e['arquivos']:
   if q.sha(q.safe(r['path']).read_bytes())!=r['sha256'] or q.sha(q.safe(r['exportado']).read_bytes())!=r['sha256']:raise ValueError('Exportação mudou')
  exports+=e['arquivos'];css=json.loads(q.safe(m['CSS']['arquivo']).read_text());cssrows+=css['registros'];cssinputs.append(m['CSS']);replay=json.loads(q.safe(m['replay']['arquivo']).read_text())
  if replay['replay_aprovados']!=count or replay['problemas']:raise ValueError('Replay do componente não aprovado')
  replayrows+=replay['resultados_replay'];components.append(dict(manifesto=q.info(p),normas=count))
 if len(names)!=total or len(mapping)!=total or len(exports)!=total or len(cssrows)!=total:raise ValueError('Seleção diferente da soma dos componentes fechados')
 normlist=out/'normas.paths.txt';normlist.write_text(''.join(p+'\n' for p in sorted(names)));add(q.info(normlist))
 # As 4.734 anteriores já estão em HEAD; reservas 921/586 são reconciliadas,
 # nunca somadas novamente. Somente os 47 ficam futuros se ainda fora de HEAD.
 cmd=[sys.executable,'-I',str(ROOT/'scripts/congelar_baseline_municipal_head_20261027.py'),'--saida',str(out/'baseline-head')]
 for p,digest in q.RESERVAS+a.reserva:cmd+=['--reserva',str(q.BASE/p),digest]
 result=subprocess.run(cmd,cwd=ROOT,check=True,capture_output=True,text=True);(out/'baseline-head.log').write_text(result.stdout+result.stderr)
 base=baseline_futuro(out/'baseline-head/manifesto.json',out/'baseline-com-reservas47')
 subprocess.run([sys.executable,'-I',str(ROOT/'scripts/comparar_baseline_municipal_head_20261027.py'),'--baseline',str(base),'--lista',str(normlist),'--saida',str(out/'confronto-conjunto.json')],cwd=ROOT,check=True)
 d=json.loads((out/'confronto-conjunto.json').read_text())
 if d['candidatos']!=total or d['colisoes']:raise ValueError('Confronto conjunto não aprovado')
 mapping_path=save('mapeamento-fontes.json',sorted(mapping,key=lambda r:r['path']));exp=save('exportacao-isolada.json',dict(normas=total,canonicos_alterados=0,arquivos=exports));save('replays-componentes.json',dict(normas=total,replay_aprovados=total,problemas=0,resultados_replay=replayrows));save('compartilhados.json',dict(paths_com_SHA_identico=sorted(set(overlaps)),divergencias=[]));save('componentes.json',components)
 active=lambda e:e['escopo'] in {'ativo','epigrafe'}
 def count(test):return sum(any(test(e) for e in r['eventos_texto_efetivo_DOM']) for r in cssrows)
 summary=dict(normas=total,fontes_especiais_ativas=count(lambda e:active(e) and e['fonte_especial_aplicada_css']),ocultacao_ativa=count(lambda e:active(e) and e['ocultacao_css']),tachado_ativo=count(lambda e:active(e) and (e['tachado_css'] or e['tags_s_del_strike'])),mso_hide_ativo=count(lambda e:active(e) and e['mso_hide_nao_padronizado']),condicionais_ou_seletores_pendentes=sum(bool(r['seletores_nao_resolvidos'] or r['regras_condicionais_com_match'] or r['pseudo_elementos_com_match']) for r in cssrows),mascaras=0,canonicos_alterados=0)
 save('CSS-conjunto.json',dict(resumo=summary,registros=cssrows,entradas=cssinputs,limite='União dos diagnósticos estáticos já aprovados por fonte/SHA, sem nova rede. CSS externo e JavaScript não executados; não certifica todo efeito visual possível.'))
 for p in out.rglob('*'):
  if p.is_file():add(q.info(p))
 add(q.info(Path(__file__).resolve()))
 for dep in a.dependencia:add(q.info(dep.resolve()))
 m=dict(normas=total,lista_normas=str(normlist.relative_to(ROOT)),mapeamento_fontes=mapping_path,exportacao_isolada=exp,componentes=components,baseline=str(base.relative_to(ROOT)),confronto=str((out/'confronto-conjunto.json').relative_to(ROOT)),arquivos=sorted(files.values(),key=lambda r:r['arquivo']),limite='Agregado imutável dos componentes explícitos. Originais preservados; reservas externas qualificadas conferidas por SHA, sem incluir os próprios componentes no baseline. Não decide vigência.')
 p=out/'manifesto.json';p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(manifesto=q.info(p),normas=total,artefatos=len(files),comparados=d['comparados'],bytes=sum(r['bytes'] for r in files.values()))))
if __name__=='__main__':main()

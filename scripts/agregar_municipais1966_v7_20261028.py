"""Congela somente os 1.278 e 688 V7, com SHA conjunto e HEAD real mais reserva 47."""
from pathlib import Path
import argparse,json,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import promover_reparos_ta47_20261028 as q
from fechar_lotes_municipais_v7_20261028 import baseline_futuro
PACKAGES=[('publicacao-novos-v7-1278-v2-20261028/manifesto.json','8a750cdde44f8dc4b766bba9f750ac28702ca9ab3ae511a1884827087594d7c6',1278),('publicacao-novos-v7-688-20261028/manifesto.json','6ef8f64ff8fd23c42a8cc739c08c93b0e71fc316b1b41690e1d731aa3df466b1',688)]

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--saida',type=Path,required=True);a=ap.parse_args();out=a.saida.resolve()
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
 for path,digest,count in PACKAGES:
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
 if len(names)!=1966 or len(mapping)!=1966 or len(exports)!=1966 or len(cssrows)!=1966:raise ValueError('Seleção diferente dos 1.966 fechados')
 normlist=out/'normas.paths.txt';normlist.write_text(''.join(p+'\n' for p in sorted(names)));add(q.info(normlist))
 # As 4.734 anteriores já estão em HEAD; reservas 921/586 são reconciliadas,
 # nunca somadas novamente. Somente os 47 ficam futuros se ainda fora de HEAD.
 cmd=[sys.executable,'-I',str(ROOT/'scripts/congelar_baseline_municipal_head_20261027.py'),'--saida',str(out/'baseline-head')]
 for p,digest in q.RESERVAS:cmd+=['--reserva',str(q.BASE/p),digest]
 result=subprocess.run(cmd,cwd=ROOT,check=True,capture_output=True,text=True);(out/'baseline-head.log').write_text(result.stdout+result.stderr)
 base=baseline_futuro(out/'baseline-head/manifesto.json',out/'baseline-com-reservas47')
 subprocess.run([sys.executable,'-I',str(ROOT/'scripts/comparar_baseline_municipal_head_20261027.py'),'--baseline',str(base),'--lista',str(normlist),'--saida',str(out/'confronto1966.json')],cwd=ROOT,check=True)
 d=json.loads((out/'confronto1966.json').read_text())
 if d['candidatos']!=1966 or d['colisoes']:raise ValueError('Confronto conjunto não aprovado')
 mapping_path=save('mapeamento-fontes.json',sorted(mapping,key=lambda r:r['path']));exp=save('exportacao-isolada1966.json',dict(normas=1966,canonicos_alterados=0,arquivos=exports));save('replays-componentes1966.json',dict(normas=1966,replay_aprovados=1966,problemas=0,resultados_replay=replayrows));save('compartilhados.json',dict(paths_com_SHA_identico=sorted(set(overlaps)),divergencias=[]));save('componentes.json',components)
 active=lambda e:e['escopo'] in {'ativo','epigrafe'}
 def count(test):return sum(any(test(e) for e in r['eventos_texto_efetivo_DOM']) for r in cssrows)
 summary=dict(normas=1966,fontes_especiais_ativas=count(lambda e:active(e) and e['fonte_especial_aplicada_css']),ocultacao_ativa=count(lambda e:active(e) and e['ocultacao_css']),tachado_ativo=count(lambda e:active(e) and (e['tachado_css'] or e['tags_s_del_strike'])),mso_hide_ativo=count(lambda e:active(e) and e['mso_hide_nao_padronizado']),condicionais_ou_seletores_pendentes=sum(bool(r['seletores_nao_resolvidos'] or r['regras_condicionais_com_match'] or r['pseudo_elementos_com_match']) for r in cssrows),mascaras=0,canonicos_alterados=0)
 save('CSS1966.json',dict(resumo=summary,registros=cssrows,entradas=cssinputs,limite='União dos diagnósticos estáticos já aprovados por fonte/SHA, sem nova rede. CSS externo e JavaScript não executados; não certifica todo efeito visual possível.'))
 for p in out.rglob('*'):
  if p.is_file():add(q.info(p))
 add(q.info(Path(__file__).resolve()))
 m=dict(normas=1966,lista_normas=str(normlist.relative_to(ROOT)),mapeamento_fontes=mapping_path,exportacao_isolada=exp,componentes=components,baseline=str(base.relative_to(ROOT)),confronto=str((out/'confronto1966.json').relative_to(ROOT)),arquivos=sorted(files.values(),key=lambda r:r['arquivo']),limite='Agregado imutável de 1.278 e 688, sem lote 21 ou outros candidatos posteriores. Originais preservados; 47 reparos externos apenas como reserva qualificada. Não decide vigência.')
 p=out/'manifesto.json';p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(manifesto=q.info(p),normas=1966,artefatos=len(files),comparados=d['comparados'],bytes=sum(r['bytes'] for r in files.values()))))
if __name__=='__main__':main()

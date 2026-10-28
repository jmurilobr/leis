"""Congela proposta de 47 reparos e evidências, preservando os pacotes anteriores."""
from pathlib import Path
import argparse,json,sys,datetime
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import promover_reparos_ta47_20261028 as q
FROZEN=[('reparos-escapes-ta-46-final-20261027/manifesto.json','47ac337b1accf282a666f7a0770ba6e9c031bc9be71619217500e8a04901e1a6'),('perfil-v7-buritis-final-20261028/manifesto.json','5efa86e88a50fc291017586e056273916dcb3875056395c5ca424b6555b1a370')]
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--saida',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);a=ap.parse_args();a.baseline=a.baseline.resolve();out=a.saida.resolve()
 if not out.is_relative_to(q.BASE):raise ValueError('Saída precisa ser privada persistente')
 out.mkdir(parents=True,exist_ok=False);files={};overlaps=[]
 def add(record):
  p=record.get('arquivo',record.get('path'));r=dict(arquivo=p,sha256=record['sha256'],bytes=record['bytes'])
  if p in files:
   if files[p]!=r:raise ValueError('Dependência congelada com SHAs divergentes: '+p)
   overlaps.append(p)
  else:files[p]=r
 for name,digest in FROZEN:
  path=q.BASE/name;m=q.verificar_manifesto(path,digest)
  for r in m['arquivos']:add(r)
  add(q.info(path))
 rows=[dict(r,modo='escapes') for r in json.loads((q.BASE/'reparos-escapes-ta-46-privado-20261027/mapa-candidatos.json').read_text())['candidatos']]
 rows.append(dict(json.loads((q.BASE/'buritis8-tachados-reparo-privado-v2-20261027/mapa-candidato.json').read_text()),modo='tachados'))
 names=[r['nome'] for r in json.loads((ROOT/'municipais/_indice/ibge-municipios.json').read_text())];proofs=[]
 for row in rows:
  _,_,proof=q.validar_linha(row,names);proofs.append(dict(path=row['path'],**proof))
 def save(name,value):
  p=out/name
  with p.open('x') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
  add(q.info(p));return str(p.relative_to(ROOT))
 mapping=save('mapa-candidatos.json',dict(candidatos=rows,promovidos=0,limite='46 escapes literais e um fecho explicitamente tachado; nenhuma inferência de revogação ou efeito atual.'))
 save('replay47.json',dict(candidatos=47,aprovados=47,retidos=0,promovidos=0,resultados=proofs))
 dedup=q.dedup(rows,a.baseline);save('dedup47.json',dedup)
 baseline=json.loads(a.baseline.read_text());add(q.info(a.baseline))
 for r in baseline['arquivos']:add(r)
 save('compartilhados.json',dict(paths_repetidos_com_sha_identico=sorted(set(overlaps)),divergencias=[]))
 for p in [Path(__file__).resolve(),ROOT/'scripts/promover_reparos_ta47_20261028.py',ROOT/'scripts/test_promover_reparos_ta47_20261028.py',ROOT/'scripts/preparar_publicacao_reparos47_20261028.py',ROOT/'scripts/congelar_baseline_municipal_head_20261027.py',ROOT/'scripts/comparar_baseline_municipal_head_20261027.py']:add(q.info(p))
 instruction=out/'INSTRUCOES_ROOT.txt';instruction.write_text('Runner: python bundled -I scripts/promover_reparos_ta47_20261028.py --manifesto ESTE_DIRETORIO/manifesto.json --sha256 SHA_ENTREGUE --saida NOVA_SAIDA_PRIVADA\nDry-run padrão, repete todas as fontes, API/M/TA público/casa/IBGE/epígrafe, V3 integral, números, tachados/atributos, matrizes, CSS e HEAD por OID com reservas921/586. Reservas já publicadas são verificadas por SHA e não somadas novamente.\nSomente ROOT pode acrescentar --apply após revisão. Ausência dos 47 no índice e HEAD é obrigatória. São reparos de candidatos privados, não de textos publicados.\nNão aplicar formatação, remoção de espaços, normalização Unicode/controles ou whitespace fix. Preservar hardbreaks e EOF. U+0002 em outros controles PV permanece intocado.\nBackups exclusivos, preparado no mesmo volume, lock consultivo e substituição atômica por arquivo. Em falha, rollback restaura somente candidatos que ainda tenham o SHA próprio; interferência externa é registrada e não sobrescrita. A transação de 47 arquivos não é um único rename.\nNão há decisão de vigência. Buritis mantém dois tachados e Secretário Substituto; remove apenas nota genérica anterior sem respaldo na fonte.\nBibliotecas já instaladas em scripts/bin/qa-*; não vendorizadas. Rodar 10 testes: python bundled -I scripts/test_promover_reparos_ta47_20261028.py\n')
 add(q.info(instruction));save('runtime.json',dict(python=sys.version,QA=['markdown-it-py==4.0.0','mdurl==0.1.2','lxml==6.1.1','html5lib==1.1','tinycss2==1.4.0','cssselect2==0.8.0','six==1.17.0','webencodings==0.5.1'],instalacao='Runtimes existentes ignorados; não incluídos no pacote.'))
 if any(r['arquivo'].endswith('.md') and not any(x.startswith('_') for x in Path(r['arquivo']).parts) for r in files.values()):raise ValueError('Pacote privado não deve incluir canônicos anteriores')
 m=dict(propostas=47,promovidas=0,mapa_candidatos=mapping,replay=str((out/'replay47.json').relative_to(ROOT)),baseline=str(a.baseline.relative_to(ROOT)),dedup=dedup,arquivos=sorted(files.values(),key=lambda r:r['arquivo']),limite='Proposta privada; publicação requer dry-run atual, decisão ROOT e promoção por preimagem. Pacotes 46 e V7 originais preservados.')
 receipt=out/'manifesto.json';receipt.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(json.dumps(q.info(receipt)))
if __name__=='__main__':main()

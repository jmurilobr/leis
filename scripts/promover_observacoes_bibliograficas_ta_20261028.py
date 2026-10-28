"""Promotor privado ROOT-only de três campos bibliográficos; dry-run padrão.

Valida manifesto/SHA, API literal HTTP 200, byte igualdade de H1+corpo e campos
anteriores, V3/CSS/M, exportação exclusiva, HEAD e reservas qualificadas. --apply
é exclusivo ROOT: backups, trocas atômicas por arquivo e rollback conservador.
Não consulta AEMERJ, não certifica vigência e não modifica o V7 congelado.
"""
from pathlib import Path
import argparse,datetime as dt,fcntl,json,subprocess,sys
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import perfil_observacao_bibliografica_ta_privado_20261028 as p
from fechar_lotes_municipais_v7_20261028 import baseline_futuro
EXTRA=[(p.q.BASE/'publicacao-agregado1966-v7-20261028/manifesto.json','d8d7b5a1ccb2ff0360f98cb6345f9009d1e2028d3d756736cef8a49d97b454b7')]

def argumentos():
 ap=argparse.ArgumentParser(description=__doc__)
 for key in ['manifesto','saida']:ap.add_argument('--'+key,type=Path,required=True)
 ap.add_argument('--sha256',required=True);ap.add_argument('--apply',action='store_true',help='Exclusivo ROOT; nunca aplicar no trabalho de preparação');ap.add_argument('--reserva',nargs=2,action='append',default=[],metavar=('RECIBO_QUALIFICADO','SHA256'));return ap

def destino(path):
 rel=Path(path)
 if rel.is_absolute() or rel.parts[0]!='municipais' or rel.suffix!='.md' or any(part.startswith(('_','.')) for part in rel.parts):raise ValueError('Destino não é norma municipal canônica')
 target=p.q.safe(path)
 for parent in target.parents:
  if parent==ROOT:break
  if parent.is_symlink():raise ValueError('Diretório do destino é symlink')
 return target

def main():
 a=argumentos().parse_args();a.manifesto=a.manifesto.resolve();out=a.saida.resolve()
 if not out.is_relative_to(p.q.BASE):raise ValueError('Saída fora dos controles persistentes')
 out.mkdir(exist_ok=False);fingerprint=p.q.sha(Path(__file__).read_bytes());m=p.q.verificar_manifesto(a.manifesto,a.sha256);rows=json.loads(p.q.safe(m['mapa_candidatos']).read_text())['candidatos']
 if len(rows)!=m['propostas'] or not rows or len({r['path'] for r in rows})!=len(rows):raise ValueError('Seleção inválida')
 if subprocess.check_output(['git','ls-files','-z','--',*[r['path'] for r in rows]],cwd=ROOT):raise ValueError('Destino já no índice; reconciliar antes de promover')
 lock=(p.q.BASE/'promocao-observacoes-bibliograficas.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);proofs=[]
 for r in rows:destino(r['path']);proofs.append(dict(path=r['path'],**p.validar_candidato(r,require_current=True)))
 command=[sys.executable,'-I',str(ROOT/'scripts/congelar_baseline_municipal_head_20261027.py'),'--saida',str(out/'baseline-head')]
 for path,digest in [(p.q.BASE/name,digest) for name,digest in p.q.RESERVAS]+EXTRA+[(Path(path).resolve(),digest) for path,digest in a.reserva]:command+=['--reserva',str(path),digest]
 subprocess.run(command,cwd=ROOT,check=True,capture_output=True);base=baseline_futuro(out/'baseline-head/manifesto.json',out/'baseline-com-reservas47');joint=p.q.dedup(rows,base);prepared=p.q.exportar(rows,out/'preparados');head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 if head!=joint['commit'] or p.q.sha(Path(__file__).read_bytes())!=fingerprint:raise ValueError('HEAD ou código mudou durante os gates; repetir em nova saída')
 result=dict(modo='apply' if a.apply else 'dry-run',propostas=len(rows),promovidas=0,manifesto=p.q.info(a.manifesto),codigo=p.q.info(Path(__file__).resolve()),dedup=joint,preparados=prepared,replays=proofs,gerado_em=dt.datetime.now(ZoneInfo('America/Recife')).isoformat(),limite='Só observacao_fonte, fonte_metadados e sha256_metadados_fonte; API atribuída literalmente. Nenhuma confirmação de AEMERJ ou vigência. Atomicidade por arquivo com rollback conservador, não um único rename de todos os destinos.')
 report=out/'resultado.json';report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 if a.apply:
  if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=head:raise ValueError('HEAD mudou antes da promoção')
  for r in rows:destino(r['path'])
  result['transacao']=p.q.aplicar_transacao(prepared,out/'backups');result['promovidas']=len(rows);report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 lock.close();print(json.dumps(dict(modo=result['modo'],propostas=len(rows),promovidas=result['promovidas'],resultado=str(report.relative_to(ROOT)))))
if __name__=='__main__':main()

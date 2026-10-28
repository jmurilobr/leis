"""Revalida proposta bibliográfica congelada, sem promover ou escrever canônicos."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import perfil_observacao_bibliografica_ta_privado_20261028 as p

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--manifesto',type=Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--saida',type=Path,required=True);a=ap.parse_args();a.manifesto=a.manifesto.resolve();m=p.q.verificar_manifesto(a.manifesto,a.sha256);rows=json.loads(p.q.safe(m['mapa_candidatos']).read_text())['candidatos'];results=[]
 if len(rows)!=m['propostas'] or len({r['path'] for r in rows})!=len(rows):raise ValueError('Seleção ambígua')
 for row in rows:
  proof=p.validar_candidato(row,require_current=False);export=a.manifesto.parent/'exportados'/row['path']
  if p.q.sha(export.read_bytes())!=row['sha256_candidato']:raise ValueError('Exportação isolada diverge')
  current=p.q.sha(p.q.safe(row['path']).read_bytes());state='preimagem intacta' if current==row['sha256_preimagem'] else 'candidato já promovido' if current==row['sha256_candidato'] else 'canônico posterior difere; esta prova só cobre snapshots'
  results.append(dict(path=row['path'],sha256_candidato=row['sha256_candidato'],estado_canonico_observado=state,sha256_canonico_observado=current,**proof))
 out=dict(candidatos=len(rows),aprovados=len(results),promovidos=0,problemas=0,resultados=results,manifesto=p.q.info(a.manifesto),limite='Replay de snapshots completos e exportações; não aplica candidatos, não confirma diário externo ou vigência. Estado do working tree é informado separadamente, sem substituir a prova histórica.')
 with a.saida.open('x') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(dict(candidatos=len(rows),aprovados=len(results),promovidos=0,problemas=0)))
if __name__=='__main__':main()

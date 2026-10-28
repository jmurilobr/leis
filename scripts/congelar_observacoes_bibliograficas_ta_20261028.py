"""Mapa privado exato de candidatos bibliográficos, sem promover ou escrever Git."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import perfil_observacao_bibliografica_ta_privado_20261028 as p

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in ['manifesto','replay','testes','saida']:ap.add_argument('--'+k,type=Path,required=True)
 ap.add_argument('--sha256',required=True);a=ap.parse_args();a.manifesto=a.manifesto.resolve();a.replay=a.replay.resolve();a.testes=a.testes.resolve();out=a.saida.resolve()
 if not out.is_relative_to(p.q.BASE):raise ValueError('Saída fora do controle privado')
 m=p.q.verificar_manifesto(a.manifesto,a.sha256);replay=json.loads(a.replay.read_text());tests=a.testes.read_text();rows=json.loads(p.q.safe(m['mapa_candidatos']).read_text())['candidatos']
 if replay['candidatos']!=len(rows) or replay['aprovados']!=len(rows) or replay['problemas'] or replay['promovidos'] or 'Ran 10 tests' not in tests or not tests.rstrip().endswith('OK'):raise ValueError('Replays/testes incompletos')
 out.mkdir(exist_ok=False);files={r['arquivo']:r for r in m['arquivos']};promotions=[];byteproof=[]
 def add(path):r=p.q.info(path);files[r['arquivo']]=r
 def save(name,value):q=out/name;q.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');add(q)
 for path in [a.manifesto,a.replay,a.testes,Path(__file__).resolve()]:add(path)
 for row in rows:
  old=p.q.safe(row['preimagem']).read_bytes();new=p.q.safe(row['candidato']).read_bytes()
  if p.q.sha(p.q.safe(row['path']).read_bytes())!=row['sha256_preimagem']:raise ValueError('Preimagem corrente mudou')
  rest_old=old.split(b'\n---\n',1)[1];rest_new=new.split(b'\n---\n',1)[1]
  if rest_old!=rest_new:raise ValueError('Corpo/H1 mudaram')
  byteproof.append(dict(path=row['path'],sha256_H1_corpo_antigo=p.q.sha(rest_old),sha256_H1_corpo_candidato=p.q.sha(rest_new),metadados_originais_intactos=True,campos_acrescentados=list(p.FIELDS)))
  promotions.append(dict(arquivo=row['path'],sha256_preimagem=row['sha256_preimagem'],sha256=row['sha256_candidato'],bytes=len(new),candidato=row['candidato'],estado='Pendente de decisão e promoção exclusiva ROOT por preimagem; não substituir arquivo publicado.'))
 save('promocoes-futuras.json',promotions);save('prova-bytes-H1-corpo.json',byteproof)
 note=out/'INSTRUCOES_ROOT.txt';note.write_text('Proposta privada: só modelo literal AEMERJ de publicação/data/edição/URL/autenticidade. Outras observações seguem retidas, inclusive outras bibliografias ainda não modeladas.\nCampos do esquema existente: observacao_fonte literal, fonte_metadados e sha256_metadados_fonte. Vinculam o JSON municipal HTTP 200. Corpo/H1, identidade, datas, notas normativas e sha256_texto permanecem byte iguais. Não consulta o diário nem certifica vigência ou equivalência.\nRepetir 10 testes e replay independente com manifesto/SHA externo deste pacote. Revalida API/M/TA público/casa/IBGE/epígrafe, contexto sem texto externo, V7, V3 integral/tachado/atributos/números/matrizes/CSS, preimagens e exportações isoladas.\nNão executar staging dos destinos futuros antes da decisão ROOT e promoção por SHA. Este agente não aplicou nada.\nO manifesto arquivos contém somente artefatos presentes; promocoes-futuras.json contém os destinos novos esperados após promoção. O staging literal futuro está em stage.paths.z, incluindo os destinos cuja preimagem ainda está no disco.\nPreservar espaços de hardbreak, EOF, caracteres e metadados originais. Não formatar nem usar git apply --whitespace=fix. Os MDs em exportados/ são cópias isoladas, não outras normas a contar.\n');add(note)
 stage=sorted(set(files)|{r['arquivo'] for r in promotions}|{str((out/n).relative_to(ROOT)) for n in ['stage.paths.z','stage.paths.txt','manifesto.json']})
 (out/'stage.paths.z').write_bytes(b'\0'.join(s.encode() for s in stage)+b'\0');add(out/'stage.paths.z');(out/'stage.paths.txt').write_text('\n'.join(stage)+'\n');add(out/'stage.paths.txt')
 result=dict(propostas=len(rows),promovidas=0,mapa_candidatos=m['mapa_candidatos'],manifesto_origem=p.q.info(a.manifesto),replay=p.q.info(a.replay),testes=p.q.info(a.testes),promocoes=str((out/'promocoes-futuras.json').relative_to(ROOT)),baseline=m['baseline'],arquivos=sorted(files.values(),key=lambda r:r['arquivo']),paths_stage=len(stage),limite='Candidatos privados, corpo/H1 intactos; nenhum canônico, V7 congelado, índice ou registro alterado.')
 q=out/'manifesto.json';q.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(manifesto=p.q.info(q),propostas=len(rows),artefatos=len(files),paths_stage=len(stage),bytes=sum(r['bytes'] for r in files.values()))))
if __name__=='__main__':main()

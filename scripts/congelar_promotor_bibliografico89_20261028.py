"""Congela promotor, dry-run e mapa futuro sem aplicar os candidatos bibliográficos."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import perfil_observacao_bibliografica_ta_privado_20261028 as p
OLD=p.q.BASE/'publicacao-observacoes-bibliograficas89-proposta-20261028/manifesto.json'
SHA='ce4f6c547a0b2ba386259d8363ae6e625198b1677c06670a62c89c35785a0652'

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--saida',type=Path,required=True);ap.add_argument('--dryrun',type=Path,required=True);ap.add_argument('--testes',type=Path,required=True);a=ap.parse_args();out=a.saida.resolve();a.dryrun=a.dryrun.resolve();a.testes=a.testes.resolve()
 if not out.is_relative_to(p.q.BASE):raise ValueError('Saída fora do controle privado')
 old=p.q.verificar_manifesto(OLD,SHA);dry=json.loads((a.dryrun/'resultado.json').read_text());test=a.testes.read_text()
 if dry['modo']!='dry-run' or dry['propostas']!=89 or dry['promovidas'] or dry['manifesto']['sha256']!=SHA or 'Ran 4 tests' not in test or not test.rstrip().endswith('OK'):raise ValueError('Dry-run ou testes não comprovados')
 rows=json.loads(p.q.safe(old['mapa_candidatos']).read_text())['candidatos'];files={r['arquivo']:r for r in old['arquivos']};out.mkdir(exist_ok=False)
 def add(path):r=p.q.info(path);files[r['arquivo']]=r
 for path in [OLD,Path(__file__).resolve(),ROOT/'scripts/promover_observacoes_bibliograficas_ta_20261028.py',ROOT/'scripts/test_promover_observacoes_bibliograficas_ta_20261028.py',a.testes]:add(path)
 for path in a.dryrun.rglob('*'):
  if path.is_file():add(path)
 promotions=json.loads(p.q.safe(old['promocoes']).read_text())
 for r in promotions:
  if p.q.sha(p.q.safe(r['arquivo']).read_bytes())!=r['sha256_preimagem'] or p.q.sha(p.q.safe(r['candidato']).read_bytes())!=r['sha256']:raise ValueError('Preimagem/candidato mudaram')
 note=out/'INSTRUCOES_ROOT.txt';note.write_text('Promotor ROOT-only, dry-run padrão. Repetir com manifesto e SHA externo deste pacote e saída nova: Python bundled -I scripts/promover_observacoes_bibliograficas_ta_20261028.py --manifesto ESTE_DIRETORIO/manifesto.json --sha256 SHA_EXTERNO --saida NOVA_SAIDA_PRIVADA\nSomente ROOT pode acrescentar --apply após revisar. Nunca usar no trabalho de preparação. Nenhuma aplicação foi executada pelo agente.\nRepete todos os 89 gates e preimagens, confirma ausência no índice e dedup HEAD real por OID mais reserva 1.966 qualificada pelo ROOT. Os 47 já publicados são reconciliados em HEAD, sem duplicação. Outras reservas qualificadas podem ser indicadas por --reserva RECIBO SHA.\nAcrescenta só observacao_fonte, fonte_metadados e sha256_metadados_fonte. Observação é literal e atribuída à API HTTP 200; não confirma AEMERJ ou vigência. H1/corpo, campos antigos, identidade, datas e sha256_texto permanecem byte iguais.\nBackups exclusivos, arquivos preparados no mesmo volume, travas consultivas, trocas atômicas por arquivo e rollback conservador. Interferência externa não é sobrescrita no rollback. Não existe uma única transação de rename para todos os arquivos.\nNão fazer staging das preimagens atuais. Somente após promoção ROOT conferir todos os destinos contra promocoes-futuras.json do pacote anterior, usando os SHAs candidatos. Então stage.paths.z é a whitelist NUL completa de artefatos e destinos futuros.\nNão formatar hardbreaks/EOF nem normalizar caracteres/metadados. Repetir os 10 testes do perfil e 4 testes do promotor.\n');add(note)
 stage=sorted(set(files)|{r['path'] for r in rows}|{str((out/n).relative_to(ROOT)) for n in ['stage.paths.z','stage.paths.txt','manifesto.json']})
 (out/'stage.paths.z').write_bytes(b'\0'.join(s.encode() for s in stage)+b'\0');add(out/'stage.paths.z');(out/'stage.paths.txt').write_text('\n'.join(stage)+'\n');add(out/'stage.paths.txt')
 m=dict(propostas=89,promovidas=0,mapa_candidatos=old['mapa_candidatos'],promocoes=old['promocoes'],pacote_anterior=p.q.info(OLD),dryrun=p.q.info(a.dryrun/'resultado.json'),testes_promotor=p.q.info(a.testes),arquivos=sorted(files.values(),key=lambda r:r['arquivo']),paths_stage=len(stage),limite='89 destinos futuros ainda na preimagem; não fazer staging antes da promoção exclusiva ROOT. Originais e V7 congelado preservados.')
 receipt=out/'manifesto.json';receipt.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(manifesto=p.q.info(receipt),artefatos=len(files),paths_stage=len(stage),bytes=sum(r['bytes'] for r in files.values()))))
if __name__=='__main__':main()

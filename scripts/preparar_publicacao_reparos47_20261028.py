"""Mapa exato pós-replay dos 47 reparos; não promove e não altera o índice."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import promover_reparos_ta47_20261028 as q

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in ['manifesto','dryrun','saida','testes']:ap.add_argument('--'+k,type=Path,required=True)
 ap.add_argument('--sha256',required=True);a=ap.parse_args();a.manifesto=a.manifesto.resolve();a.dryrun=a.dryrun.resolve();a.testes=a.testes.resolve();out=a.saida.resolve()
 if not out.is_relative_to(q.BASE):raise ValueError('Saída fora dos controles privados')
 out.mkdir(parents=True,exist_ok=False);m=q.verificar_manifesto(a.manifesto,a.sha256);rows=json.loads(q.safe(m['mapa_candidatos']).read_text())['candidatos'];dry=json.loads((a.dryrun/'resultado.json').read_text())
 if dry['modo']!='dry-run' or dry['propostas']!=47 or dry['promovidas']!=0 or dry['manifesto']['sha256']!=a.sha256:raise ValueError('Dry-run não corresponde ao pacote')
 if len(dry['resultados'])!=47 or any(not r['replay']['aprovado'] for r in dry['resultados']):raise ValueError('Replay incompleto')
 tests=a.testes.read_text()
 if 'Ran 10 tests' not in tests or not tests.rstrip().endswith('OK'):raise ValueError('Recibo de testes não prova 10 aprovados')
 files={r['arquivo']:r for r in m['arquivos']};files[str(a.manifesto.relative_to(ROOT))]=q.info(a.manifesto)
 for p in a.dryrun.rglob('*'):
  if p.is_file():files[str(p.relative_to(ROOT))]=q.info(p)
 files[str(a.testes.relative_to(ROOT))]=q.info(a.testes)
 for p in [Path(__file__).resolve(),ROOT/'scripts/promover_reparos_ta47_20261028.py',ROOT/'scripts/test_promover_reparos_ta47_20261028.py']:files[str(p.relative_to(ROOT))]=q.info(p)
 def save(name,data,binary=False):
  p=out/name
  if binary:p.write_bytes(data)
  else:p.write_text(data)
  files[str(p.relative_to(ROOT))]=q.info(p)
 def js(name,value):save(name,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 promotion=[];whitespace=[];sources=[]
 for r in rows:
  old=q.safe(r['path']).read_bytes();new=q.safe(r['candidato']).read_bytes()
  if q.sha(old)!=r['sha256_preimagem'] or q.sha(new)!=r['sha256_candidato']:raise ValueError('Pré-condição de promoção mudou')
  promotion.append(dict(arquivo=r['path'],sha256=r['sha256_candidato'],bytes=len(new),preimagem_sha256=r['sha256_preimagem'],candidato=r['candidato'],modo=r['modo'],estado='Exclusivamente ROOT: pendente de promoção por preimagem antes de staging.'))
  mr=q.material(r);sources.append(dict(path=r['path'],sha256_candidato=r['sha256_candidato'],prova_frontend=mr['prova_frontend'],prova_norma=mr['prova_norma'],prova_ta=mr['prova_ta'],prova_casa=mr['prova_casa']))
  lines=new.splitlines();whitespace.append(dict(path=r['path'],hardbreaks=sum(x.endswith(b'  ') for x in lines),EOF_hex=new[-16:].hex(),CRLF=new.count(b'\r\n'),controles_U0002=new.count(b'\x02')))
 js('promocoes47.json',promotion);js('mapeamento-fontes47.json',sources);js('whitespace.json',whitespace);save('normas.paths.txt',''.join(r['path']+'\n' for r in rows))
 save('INSTRUCOES_ROOT.txt','47 normas pendentes de promoção por ROOT. Não fazer staging de preimagens.\nRepetir runner com --manifesto e SHA externos entregues, saída nova; padrão dry-run. Somente ROOT acrescenta --apply. Depois conferir cada destino contra promocoes47.json e verificar recibo de aplicação antes do staging.\nManter os metadados originais; somente sha256_texto difere. Buritis mantém os dois tachados e Secretário Substituto, sem inferência jurídica. Controles U+0002 das outras normas PV não foram tocados.\nNão rodar formatador, strip, normalizador Unicode ou git apply --whitespace=fix. Preservar hardbreaks/EOF.\nStaging exclusivamente ROOT: git --literal-pathspecs -c core.autocrlf=false add -f --pathspec-from-file=ESTE_DIRETORIO/stage.paths.z --pathspec-file-nul\nConfrontar blobs do índice com manifesto arquivos e promocoes47.json; conferir SHA externo do próprio manifesto. O mapa tem destinos futuros, cujos bytes atuais ainda são a preimagem: isso é explícito e impede publicação acidental sem a promoção.\nReservas921/586 qualificadas serão reconciliadas por SHA contra HEAD a cada dry-run; não contam duas vezes quando publicadas.\n')
 js('stage.expected.json',dict(artefatos_presentes=list(sorted(files.values(),key=lambda r:r['arquivo'])),destinos_futuros=promotion))
 paths=sorted(set(files)|{r['path'] for r in rows}|{str((out/n).relative_to(ROOT)) for n in ['stage.paths.z','stage.paths.txt','manifesto.json']})
 save('stage.paths.z',b'\0'.join(p.encode() for p in paths)+b'\0',True);save('stage.paths.txt','\n'.join(paths)+'\n')
 result=dict(propostas=47,promovidas=0,artefatos=len(files),paths_stage=len(paths),manifesto_sucessor=q.info(a.manifesto),dryrun=q.info(a.dryrun/'resultado.json'),testes=q.info(a.testes),promocoes=str((out/'promocoes47.json').relative_to(ROOT)),arquivos=sorted(files.values(),key=lambda r:r['arquivo']),limite='Proposta exata: artefatos presentes e 47 destinos futuros sujeitos à promoção ROOT; nenhum canônico, índice ou pacote anterior modificado.')
 receipt=out/'manifesto.json';receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(q.info(receipt)));print(json.dumps(dict(propostas=47,artefatos=len(files),paths_stage=len(paths))))
if __name__=='__main__':main()

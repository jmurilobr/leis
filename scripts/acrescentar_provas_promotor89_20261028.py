"""Overlay imutável com testes adicionais de concorrência; sem aplicar ou Git."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import perfil_observacao_bibliografica_ta_privado_20261028 as p
OLD=p.q.BASE/'promotor-bibliografico89-final-20261028/manifesto.json'
SHA='28cb4ed1c91fde673e085a84558c6a87c0f5b1c07327821084719ffb847754e8'

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--saida',type=Path,required=True);a=ap.parse_args();out=a.saida.resolve();m=p.q.verificar_manifesto(OLD,SHA)
 if not out.is_relative_to(p.q.BASE):raise ValueError('Saída fora dos controles privados')
 log=p.q.BASE/'observacoes-bibliograficas-rollback-concorrencia-testes-20261028.txt';text=log.read_text()
 if 'Ran 2 tests' not in text or not text.rstrip().endswith('OK'):raise ValueError('Dois testes suplementares não passaram')
 out.mkdir(exist_ok=False);files={r['arquivo']:r for r in m['arquivos']}
 def add(path):r=p.q.info(path);files[r['arquivo']]=r
 for path in [OLD,log,ROOT/'scripts/test_rollback_bibliografico_concorrencia_20261028.py',Path(__file__).resolve()]:add(path)
 rows=json.loads(p.q.safe(m['mapa_candidatos']).read_text())['candidatos']
 if len(rows)!=89:raise ValueError('Seleção diferente dos 89')
 for r in rows:
  if p.q.sha(p.q.safe(r['path']).read_bytes())!=r['sha256_preimagem']:raise ValueError('Preimagem mudou')
 note=out/'INSTRUCOES_ROOT.txt';note.write_text('Overlay final do promotor ROOT-only. Preserva todos os mapas anteriores.\nUsar manifesto e SHA externo deste diretório no promotor; --apply só ROOT, saída sempre nova. Dry-run é padrão. A preparação não executou --apply.\nTestes: 10 de bibliografia literal/negativos/bytes, 4 de promoção e mais 2 de rollback com interferência externa e diretório symlink em raiz isolada. Os 16 passaram; os testes adicionais não alteraram o promotor congelado.\nNão stagear preimagens atuais: primeiro promover por SHA e confirmar cada destino futuro contra promocoes-futuras.json do pacote anterior; só então usar stage.paths.z.\nOs artefatos presentes estão em arquivos; os 89 destinos futuros estão exclusivamente no mapa de promoções. Corpo/H1/identidade/captura e campos anteriores permanecem byte iguais, com apenas três campos bibliográficos da fonte acrescidos. API atribuída, sem certificar AEMERJ ou vigência.\n');add(note)
 stage=sorted(set(files)|{r['path'] for r in rows}|{str((out/n).relative_to(ROOT)) for n in ['stage.paths.z','stage.paths.txt','manifesto.json']})
 (out/'stage.paths.z').write_bytes(b'\0'.join(x.encode() for x in stage)+b'\0');add(out/'stage.paths.z');(out/'stage.paths.txt').write_text('\n'.join(stage)+'\n');add(out/'stage.paths.txt')
 m.update(pacote_anterior_overlay=p.q.info(OLD),testes_suplementares=p.q.info(log),arquivos=sorted(files.values(),key=lambda r:r['arquivo']),paths_stage=len(stage));receipt=out/'manifesto.json';receipt.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(manifesto=p.q.info(receipt),artefatos=len(files),paths_stage=len(stage),bytes=sum(r['bytes'] for r in files.values()))))
if __name__=='__main__':main()

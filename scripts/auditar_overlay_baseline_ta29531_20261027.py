"""Fecha diferença de escopo 770/771 sem modificar listas ou recibos antigos."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from auditar_colisoes_lote_municipal import keys

BASE=Path('municipais/_indice/_recuperacao_20261027')
MISSING='municipais/RO/porto-velho/decretos/2026/decretos-22256-2026-sapl-29531.md'
ORIG=Path('municipais/_lotes/20261021-textos-articulados-agregado-771/normas.paths.txt')
FULL=ORIG.with_name('normas-apos-promocao.paths.txt')
GROUPS=[(286,'ta-contexto-0001'),(393,'ta-contexto-0002'),(603,'ta-contexto-0003'),
        (673,'ta-contexto-0004'),(907,'tabelas-contexto-0003'),(509,'ta-contexto-0005')]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(p,value):
    with p.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--saida',type=Path,required=True);a=ap.parse_args()
    old=set(ORIG.read_text().splitlines());full=set(FULL.read_text().splitlines())
    assert full-old=={MISSING} and not old-full
    head=subprocess.check_output(['git','rev-parse','HEAD']).decode().strip()
    blob=subprocess.check_output(['git','show','HEAD:'+MISSING])
    assert blob==Path(MISSING).read_bytes(),'Baseline faltante não corresponde ao HEAD'
    missing_keys=set(keys(blob.decode(),MISSING));results=[];files={str(ORIG),str(FULL),MISSING,str(Path(__file__).relative_to(Path.cwd()))}
    a.saida.mkdir(parents=True,exist_ok=False)
    for count,context in GROUPS:
        receipt=BASE/f'agregado{count}-final/entrega-final.json'
        manifest=json.loads(receipt.read_text());records={r['arquivo']:r for r in manifest['arquivos']}
        norms=Path(manifest['lista_normas']);collision=BASE/'lotes'/context/'colisoes-globais.json'
        assert sha(collision)==records[str(collision)]['sha256']
        assert sha(norms)==records[str(norms)]['sha256']
        prior=json.loads(collision.read_text());assert not prior['colisoes']
        names=set()
        for proof in prior['fontes']:
            p=Path(proof['arquivo']);assert sha(p)==proof['sha256']
            names.update(x for x in p.read_text().replace('\0','\n').splitlines() if x.startswith('municipais/') and x.endswith('.md') and not any(t.startswith('_') for t in Path(x).parts))
        assert len(names)==prior['comparados'] and MISSING not in names
        conflicts=[]
        for p in norms.read_text().splitlines():
            common=missing_keys.intersection(keys(Path(p).read_text(),p))
            if common:conflicts.append(dict(path=p,chaves=sorted(common)))
        result=dict(normas=count,recibo=str(receipt),recibo_sha256=sha(receipt),lista_normas=str(norms),lista_sha256=sha(norms),
            controle_anterior=str(collision),controle_anterior_sha256=sha(collision),
            baseline_anterior=len(names),baseline_completa=len(names|{MISSING}),
            caminho_suplementar=MISSING,colisoes_suplementares=conflicts,
            prova='O controle anterior sem colisões cobre exatamente o conjunto anterior. A única diferença da lista após promoção é o caminho suplementar, comparado integralmente por URL e identidade contra todas as normas desta seleção. Não altera nem substitui o controle anterior.')
        assert not conflicts
        results.append(result);files.update([str(receipt),str(norms),str(collision)])
    # Além da prova por diferença de conjuntos, a seleção nova 509 recebe
    # comparação direta completa com todas as listas e o caminho faltante.
    last=json.loads((BASE/'lotes/ta-contexto-0005/colisoes-globais.json').read_text())
    lists=[r['arquivo'] for r in last['fontes']]+[str(FULL)]
    command=[sys.executable,'-I','scripts/auditar_colisoes_lote_municipal.py','--baseline',lists[0]]
    for p in lists[1:]:command+=['--adicional',p]
    command+=['--lista',str(BASE/'agregado509-final/normas.paths.txt'),'--saida',str(a.saida/'509-colisoes-baseline-completa.json')]
    subprocess.run(command,check=True)
    complete=json.loads((a.saida/'509-colisoes-baseline-completa.json').read_text())
    assert complete['comparados']==22771 and complete['candidatos']==509 and not complete['colisoes']
    dump(a.saida/'controle.json',dict(motivo='A expansão automática usou a lista de 770 normas do agregado771, omitindo o candidato 29531 promovido. A lista após promoção possui 771. Corrigido por overlay, sem alteração de máscaras, fontes ou pacotes anteriores.',
        lista_770=dict(path=str(ORIG),sha256=sha(ORIG)),lista_771=dict(path=str(FULL),sha256=sha(FULL)),
        caminho_faltante=dict(path=MISSING,sha256=sha(MISSING),head=head,git_blob_sha256=hashlib.sha256(blob).hexdigest()),
        resultados=results,limite='Este overlay trata exclusivamente da diferença de escopo do baseline. Não certifica atualização ou vigência jurídica.'))
    for p in lists:files.add(p)
    files.add('scripts/auditar_colisoes_lote_municipal.py')
    files.update(str(p) for p in a.saida.iterdir() if p.is_file())
    paths=a.saida/'artefatos.paths.txt';paths.write_text('\n'.join(sorted(files))+'\n');files.add(str(paths))
    rows=[dict(arquivo=p,sha256=sha(p),bytes=Path(p).stat().st_size) for p in sorted(files)]
    receipt=a.saida/'manifesto.json';dump(receipt,dict(arquivos=rows,bytes=sum(r['bytes'] for r in rows),selecao_nova509=str(BASE/'agregado509-final/entrega-final.json'),resultados=results))
    print(json.dumps(dict(manifesto=str(receipt),sha256=sha(receipt),arquivos=len(rows))))


if __name__=='__main__':main()

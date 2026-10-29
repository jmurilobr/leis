"""Replay AP sem rede/Git/escrita canônica; dependências QA externas explícitas."""
import argparse,gzip,hashlib,json,sys,tempfile,subprocess
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--raiz',required=True);p.add_argument('--manifesto',required=True);p.add_argument('--qa',required=True);p.add_argument('--qa-html5',required=True);p.add_argument('--controle',required=True);p.add_argument('--reinventariar',action='store_true');a=p.parse_args()
    root=Path(a.raiz).resolve();manifest=root/a.manifesto;m=json.loads(manifest.read_text());out=Path(a.controle);out.mkdir(parents=True,exist_ok=False)
    sha=lambda b:hashlib.sha256(b).hexdigest()
    for name,digest in m['arquivos'].items():
        rel=Path(name)
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('caminho não portátil')
        if sha((root/rel).read_bytes())!=digest:raise ValueError('SHA divergente: '+name)
    sys.path[:0]=[str(Path(a.qa).resolve()),str(Path(a.qa_html5).resolve()),str(Path(__file__).resolve().parent)]
    from auditar_constituicao_ap import projecao_markdown,auditar
    from representar_constituicao_ap import propor,extrair_documento
    from verificar_motores_ap import comparar
    original=(root/m['preimagem']).read_bytes();receipt=json.loads((root/m['inventario_recibo']).read_text())
    raw=gzip.decompress((root/m['inventario_prova']).read_bytes());proof=[json.loads(x) for x in raw.decode().splitlines()]
    if a.reinventariar:
        fresh=out/'reinventario';auditar(root/m['cache_original'],root/m['preimagem'],fresh,None)
        again=gzip.decompress((fresh/'prova-caracteres.jsonl.gz').read_bytes())
        if again!=raw:raise ValueError('inventário geométrico não reproduzido literalmente')
    capture=json.loads((root/m['recaptura']).read_text());blob,h=propor(original,proof,receipt,capture,m['destino_pdf'])
    if blob!=(root/m['candidato']).read_bytes():raise ValueError('candidato não reproduzido')
    editorial=extrair_documento(blob)
    if editorial!=(root/m['material_nao_tachado']).read_text():raise ValueError('extração explícita divergiu')
    old=original.split(b'\n---\n',1)[1].decode();new=blob.split(b'\n---\n',1)[1].decode()
    selected={i for run in h['historico'] for i in range(run['inicio_unicode'],run['fim_unicode']) if not old[i].isspace()}
    compact,positions,*_=projecao_markdown(old);pairs=[(rank,old[pos]) for rank,pos in enumerate(positions) if pos in selected]
    motors=comparar(old,new,pairs,out/'motores')
    # Testes herdam somente caminhos explícitos, inclusive sob Python -I.
    import unittest
    suite=unittest.defaultTestLoader.discover(str(Path(__file__).parent),pattern='test_*.py')
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():raise ValueError('regressões falharam')
    r=dict(arquivos_SHA_conferidos=len(m['arquivos']),paginas=len(proof),caracteres_tachados=len(pairs),segmentos=h['total_segmentos'],motores=motors,reinventario_geometrico=a.reinventariar,testes=result.testsRun,sha256_candidato=sha(blob),apendices_byte_identicos=h['apendices_byte_identicos'],novas_normas=0,rede=False,escrita_canonica=False)
    (out/'recibo.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['arquivos_SHA_conferidos','paginas','caracteres_tachados','testes','novas_normas']}))

if __name__=='__main__':main()

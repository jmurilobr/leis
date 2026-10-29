"""Replay offline MG11, leitura de seleção e fontes congeladas, nenhuma promoção."""
import argparse,json,sys,hashlib,unittest
from pathlib import Path
def main():
    p=argparse.ArgumentParser();p.add_argument('--raiz',required=True);p.add_argument('--manifesto',required=True);p.add_argument('--qa',required=True);p.add_argument('--controle',required=True);a=p.parse_args();root=Path(a.raiz).resolve();m=json.loads((root/a.manifesto).read_text());out=Path(a.controle);out.mkdir(parents=True,exist_ok=False)
    for name,digest in m['arquivos'].items():
        rel=Path(name)
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('path inválido')
        if hashlib.sha256((root/rel).read_bytes()).hexdigest()!=digest:raise ValueError(name)
    sys.path[:0]=[str(Path(a.qa).resolve()),str(Path(__file__).resolve().parent)]
    from auditar_mg import auditar
    proof=[auditar(root,d) for d in m['documentos']]
    for d in m['documentos']:
        if (root/d['path']).read_bytes()!=(root/d['candidato']).read_bytes():raise ValueError('candidato mudou corpo/cabeçalho')
    dedup=json.loads((root/m['dedup']).read_text());tree=(root/m['tree']).read_bytes();paths=[v.split(b'\t',1)[1].decode() for v in tree.split(b'\0') if b'\t' in v]
    for d in m['documentos']:
        target=Path(d['path']);key=target.stem.rsplit('-',1)[0]
        if any(Path(x).parts[2]==target.parts[2] and Path(x).stem.rsplit('-',1)[0]==key for x in paths):raise ValueError('colisão HEAD tipo/número, mesmo sem ano')
    tests=unittest.TextTestRunner().run(unittest.defaultTestLoader.discover(str(Path(__file__).parent),pattern='test_*.py'))
    if not tests.wasSuccessful():raise ValueError('testes falharam')
    receipt=dict(total=len(proof),documentos=proof,testes=tests.testsRun,arquivos_SHA=len(m['arquivos']),HEAD=dedup['HEAD'],rede=False,promovidas=0,corpos_candidatos_byte_identicos=True)
    (out/'recibo.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(total=len(proof),testes=tests.testsRun)))
if __name__=='__main__':main()

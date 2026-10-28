"""Compara candidatos com metadados dos blobs HEAD e reservas qualificadas."""
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from auditar_colisoes_lote_municipal import keys


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--lista',type=Path,required=True);ap.add_argument('--saida',type=Path,required=True);a=ap.parse_args()
    manifest=json.loads(a.baseline.read_text());source=Path(manifest['metadados'])
    for record in manifest['arquivos']:
        p=Path(record['arquivo'])
        assert p.is_file() and sha(p)==record['sha256'] and p.stat().st_size==record['bytes'],str(p)
    proof=next(r for r in manifest['arquivos'] if r['arquivo']==str(source))
    assert sha(source)==proof['sha256'] and source.stat().st_size==proof['bytes']
    index=collections.defaultdict(set);bindings={}
    with gzip.open(source,'rt') as f:
        for line in f:
            r=json.loads(line);assert r['path'] not in bindings;bindings[r['path']]={k:r[k] for k in ['oid','sha256','origem']}
            for key in r['chaves']:index[tuple(key)].add(r['path'])
    assert len(bindings)==manifest['total']
    candidates=a.lista.read_text().splitlines();assert len(candidates)==len(set(candidates))
    collisions=[];hashes={}
    for path in candidates:
        raw=Path(path).read_bytes();hashes[path]=hashlib.sha256(raw).hexdigest()
        for key in keys(raw.decode(),path):
            if index[key]:
                existing=[]
                for p in sorted(index[key]):
                    binding=bindings[p] if p in bindings else dict(oid=None,sha256=hashes[p],origem='candidato anterior deste lote')
                    existing.append(dict(path=p,**binding))
                collisions.append(dict(path=path,chave=key,existentes=existing))
            index[key].add(path)
    result=dict(commit=manifest['commit'],baseline=str(a.baseline),sha256_baseline=sha(a.baseline),
        comparados=len(bindings),candidatos=len(candidates),colisoes=collisions,
        fontes=[dict(arquivo=str(a.baseline),sha256=sha(a.baseline))],
        lista=str(a.lista),sha256_lista=sha(a.lista),sha256_candidatos=hashes,
        criterio='URLs oficiais e identidade IBGE/rota/tipo/número/ano. O índice usa somente metadados do blob integral por OID do commit registrado e reservas qualificadas com SHA conferido; não lê versões do working tree para substituir HEAD.',codigo_sha256=sha(__file__))
    with a.saida.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(comparados=len(bindings),candidatos=len(candidates),colisoes=len(collisions))))
    return int(bool(collisions))


if __name__=='__main__':raise SystemExit(main())

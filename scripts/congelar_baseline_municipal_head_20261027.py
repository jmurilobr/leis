"""Snapshot integral de metadados dos blobs municipais de um commit e reservas.

Git é usado apenas para leitura: rev-parse, ls-tree restrito a municipais e
cat-file por OID. Nenhum cabeçalho é truncado ou substituído pelo working tree.
"""
import argparse
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parent))
from auditar_colisoes_lote_municipal import keys
from auditar_municipal import metadados

ROOT=Path(__file__).resolve().parent.parent


def sha(b):return hashlib.sha256(b).hexdigest()


def norma(path):
    return path.startswith('municipais/') and path.endswith('.md') and not any(p.startswith(('_','.')) for p in Path(path).parts)


def registro(path,oid,raw,origem):
    text=raw.decode('utf-8')
    if not text.startswith('---\n') or '\n---\n' not in text[4:]:
        raise ValueError('Cabeçalho integral inválido: '+path)
    header=text[4:].split('\n---\n',1)[0]
    return dict(path=path,oid=oid,sha256=sha(raw),bytes=len(raw),origem=origem,
                cabecalho_integral=header,metadados=metadados(text),chaves=keys(text,path))


def reservas(receipt,expected,head):
    raw=receipt.read_bytes()
    if sha(raw)!=expected:raise ValueError('SHA do recibo de reserva diverge')
    manifest=json.loads(raw);index={r['arquivo']:r for r in manifest['arquivos']}
    # A reserva foi explicitamente indicada como qualificada pelo operador.
    # Conferir todos os artefatos antes de aproveitar seus caminhos canônicos.
    for path,r in index.items():
        b=(ROOT/path).read_bytes()
        if sha(b)!=r['sha256'] or len(b)!=r['bytes']:raise ValueError('Artefato de reserva mudou: '+path)
    lista=manifest.get('lista_normas') or manifest['listas']['normas']
    assert lista in index
    names=(ROOT/lista).read_text().splitlines()
    if len(names)!=manifest['normas'] or len(set(names))!=len(names):raise ValueError('Cardinalidade de reserva divergente')
    records=[];already=[]
    for path in names:
        if not norma(path) or path not in index:raise ValueError('Reserva sem norma canônica vinculada')
        b=(ROOT/path).read_bytes();r=registro(path,None,b,'reserva qualificada')
        r['recibo_reserva']=str(receipt.relative_to(ROOT));r['sha256_recibo_reserva']=expected
        if path in head:
            if head[path]['sha256']!=r['sha256']:raise ValueError('Reserva diverge do blob HEAD: '+path)
            already.append(path)
        else:records.append(r)
    return records,dict(recibo=str(receipt.relative_to(ROOT)),sha256=expected,normas=len(names),ja_no_head=already,adicionadas=len(records))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--saida',type=Path,required=True)
    ap.add_argument('--reserva',nargs=2,action='append',default=[],metavar=('RECIBO','SHA256'))
    a=ap.parse_args();a.saida=a.saida.resolve();a.saida.mkdir(parents=True,exist_ok=False)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    tree=subprocess.check_output(['git','ls-tree','-r','-z','--full-tree',commit,'--','municipais'],cwd=ROOT)
    (a.saida/'ls-tree-municipais.z').write_bytes(tree)
    selected=[]
    for entry in tree.split(b'\0'):
        if not entry:continue
        desc,path=entry.split(b'\t',1);mode,kind,oid=desc.decode().split();path=path.decode()
        if norma(path):
            if kind!='blob' or mode not in {'100644','100755'}:raise ValueError('Norma não é blob regular: '+path)
            selected.append((path,oid))
    process=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    records={}
    try:
        for path,oid in selected:
            process.stdin.write((oid+'\n').encode());process.stdin.flush()
            got,kind,size=process.stdout.readline().split()
            if got.decode()!=oid or kind!=b'blob':raise ValueError('cat-file devolveu objeto inesperado')
            raw=process.stdout.read(int(size))
            if len(raw)!=int(size) or process.stdout.read(1)!=b'\n':raise ValueError('Blob incompleto')
            records[path]=registro(path,oid,raw,'HEAD')
    finally:
        process.stdin.close();process.stdout.close()
        if process.wait()!=0:raise RuntimeError('cat-file falhou')
    reserves=[]
    for path,expected in a.reserva:
        rows,proof=reservas((ROOT/path).resolve(),expected,records)
        for r in rows:
            if r['path'] in records:raise ValueError('Reservas repetidas')
            records[r['path']]=r
        reserves.append(proof)
    output=a.saida/'metadados-integrais.jsonl.gz'
    with gzip.open(output,'wt',encoding='utf-8',compresslevel=1) as f:
        for path in sorted(records):f.write(json.dumps(records[path],ensure_ascii=False)+'\n')
    (a.saida/'normas.paths.txt').write_text('\n'.join(sorted(records))+'\n')
    files=[output,a.saida/'normas.paths.txt',a.saida/'ls-tree-municipais.z',Path(__file__).resolve(),
           ROOT/'scripts/auditar_colisoes_lote_municipal.py',ROOT/'scripts/auditar_municipal.py']
    manifest=dict(commit=commit,escopo='git ls-tree -r -z COMMIT -- municipais; somente Markdown canônico regular',
        capturado_em=dt.datetime.now(ZoneInfo('America/Recife')).isoformat(),normas_head=len(selected),
        reservas=reserves,total=len(records),metadados=str(output.relative_to(ROOT)),
        arquivos=[dict(arquivo=str(p.relative_to(ROOT)),sha256=sha(p.read_bytes()),bytes=p.stat().st_size) for p in files],
        limite='Metadados extraídos do blob completo por OID; cabeçalhos literais integrais preservados. Snapshot não certifica vigência ou identidade correta do acervo anterior.')
    receipt=a.saida/'manifesto.json'
    with receipt.open('x') as f:json.dump(manifest,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(manifesto=str(receipt.relative_to(ROOT)),sha256=sha(receipt.read_bytes()),commit=commit,head=len(selected),reservas_adicionadas=len(records)-len(selected),total=len(records))))


if __name__=='__main__':main()

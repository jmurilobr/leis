"""Confronto independente CONFAZ/DOU v3 por identidade, usando blobs reais de HEAD.

Reutiliza o índice ROOT v8 conferido por OID, atualiza diferenças do commit
por blobs integrais e reexamina títulos/metadados dos possíveis aliases.
Nenhuma edição de canônicos, índice Git ou rede.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from confaz_auditar_piloto_privado_v2_20261027 import normal,identidade,MarkdownIt,texto_visivel_html
from auditar_cache_dou import meta_corpo


def sha(b):return hashlib.sha256(b).hexdigest()


def canonical(path):return path.startswith('reguladores/') and path.endswith('.md') and not any(p.startswith(('_','.')) for p in Path(path).parts)


def potential(path,meta):
    value=normal(str(meta.get('tipo',''))+' '+str(meta.get('orgao',''))+' '+path)
    return 'CONVENIO' in value or 'CONFAZ' in value or 'CONSELHO NACIONAL DE POLITICA FAZENDARIA' in value


def read_blobs(pairs):
    proc=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    try:
        for path,oid in pairs:
            proc.stdin.write((oid+'\n').encode());proc.stdin.flush()
            got,kind,size=proc.stdout.readline().split();assert got.decode()==oid and kind==b'blob'
            raw=proc.stdout.read(int(size));assert len(raw)==int(size) and proc.stdout.read(1)==b'\n'
            yield path,oid,raw
    finally:
        proc.stdin.close();proc.stdout.close()
        if proc.wait()!=0:raise RuntimeError('cat-file falhou')


def label_key(text,data=None):
    try:
        parsed=identidade(text);return (parsed['tipo'],parsed['numero'],parsed['ano'])
    except (ValueError,KeyError):pass
    m=re.match(r'^CONVENIO\s+ICMS\s+(?:N[.O]*\s*)?(\d+)\s*/\s*(\d{2}|\d{4})\b',normal(text))
    if not m:return None
    n,year=m.groups()
    if len(year)==2:
        known=re.match(r'^(\d{4})-',str(data or ''))
        if not known or int(known[1])%100!=int(year):return None
        year=known[1]
    return ('Convênio ICMS',int(n),int(year))


def metadata_key(meta):
    title=label_key(str(meta.get('titulo','')),meta.get('data'))
    if title:return title
    kind=normal(str(meta.get('tipo','')));agency=normal(str(meta.get('orgao','')))
    if 'CONVENIO' not in kind or not ('ICMS' in kind or 'CONFAZ' in agency or 'CONSELHO NACIONAL DE POLITICA FAZENDARIA' in agency):return None
    n=re.fullmatch(r'\s*(\d[\d.]*)(?:/\d{2,4})?\s*',str(meta.get('numero','')))
    year=re.match(r'^(\d{4})-',str(meta.get('data','')))
    if n and year:return ('Convênio ICMS',int(n[1].replace('.','')),int(year[1]))
    return None


def key(meta,body,engine):
    lines=body.lstrip('\n').splitlines()
    if lines and lines[0].startswith('# '):lines=lines[1:]
    visible=texto_visivel_html(engine.render('\n'.join(lines)))
    identity=label_key(visible,meta.get('data'))
    if not identity:return None
    if 'CONFAZ' not in normal(str(meta.get('orgao',''))+' '+visible[:5000]) and 'CONSELHO NACIONAL DE POLITICA FAZENDARIA' not in normal(visible[:5000]):return None
    return identity


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--qa',type=Path,required=True);ap.add_argument('--saida',type=Path,required=True);a=ap.parse_args()
    a.saida.mkdir(parents=True,exist_ok=False)
    baseline_path=ROOT/'scripts/dados/baseline-reguladores-head-v8-20261027.json'
    baseline=json.loads(baseline_path.read_text());cache=ROOT/baseline['cache'];assert sha(cache.read_bytes())==baseline['sha256_cache']
    index=json.loads(gzip.decompress(cache.read_bytes()));assert index['baseline_sha256']==baseline['baseline_sha256']
    headers={r['path']:r['meta'] for r in index['documentos'] if canonical(r['path'])}
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    subprocess.run(['git','merge-base','--is-ancestor',baseline['head'],head],cwd=ROOT,check=True)
    tree=subprocess.check_output(['git','ls-tree','-r','-z','--full-tree',head,'--','reguladores'],cwd=ROOT)
    (a.saida/'ls-tree-reguladores.z').write_bytes(tree)
    objects={}
    for entry in tree.split(b'\0'):
        if not entry:continue
        info,path=entry.split(b'\t',1);mode,kind,oid=info.decode().split();path=path.decode()
        if canonical(path):
            if kind!='blob' or mode not in {'100644','100755'}:raise ValueError('Normativo não é blob regular')
            objects[path]=oid
    changes=subprocess.check_output(['git','diff','--name-status','--no-renames','-z',baseline['head'],head,'--','reguladores'],cwd=ROOT).split(b'\0')
    delta=[]
    for i in range(0,len(changes)-1,2):
        status=changes[i].decode();path=changes[i+1].decode()
        if not canonical(path):continue
        if status=='D':headers.pop(path,None)
        else:delta.append((path,objects[path]))
    delta_records=[]
    for path,oid,raw in read_blobs(delta):
        meta,_=meta_corpo(raw.decode());headers[path]=meta
        delta_records.append(dict(path=path,oid=oid,sha256=sha(raw),bytes=len(raw),metadados_completos=meta))
    assert set(headers)==set(objects),'Índice v8 + delta não cobre exatamente HEAD canônico'
    with gzip.open(a.saida/'delta-metadados-completos.jsonl.gz','wt',encoding='utf-8') as f:
        for r in delta_records:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    qa=json.loads((a.qa/'resumo.json').read_text());targets={('Convênio ICMS',r['identidade']['numero'],r['identidade']['ano']) for r in qa['resultados'] if r.get('identidade')}
    engine=MarkdownIt('commonmark',{'html':True}).enable('table').enable('strikethrough');matches=[];uncertain=[];examined=0
    pairs=[(p,objects[p]) for p in sorted(headers) if potential(p,headers[p])]
    for path,oid,raw in read_blobs(pairs):
        examined+=1;meta,body=meta_corpo(raw.decode());identity=key(meta,body,engine)
        record=dict(path=path,oid=oid,sha256=sha(raw),bytes=len(raw),metadados_completos=meta)
        if identity in targets:matches.append(dict(identidade=identity,**record))
        else:
            # Preserva como dúvida uma identidade indexada que coincida, mas
            # cujo corpo não confirme a epígrafe. Não vira norma nova por falha
            # de qualidade do registro já publicado.
            possible=metadata_key(meta)
            if possible in targets:uncertain.append(dict(identidade=possible,motivo='Título indexado coincide; epígrafe independente do corpo não confirmada',**record))
    rows=[]
    for r in qa['resultados']:
        identity=r.get('identidade');k=(identity['tipo'],identity['numero'],identity['ano']) if identity else None
        aliases=[x for x in matches if tuple(x['identidade'])==k];doubts=[x for x in uncertain if tuple(x['identidade'])==k]
        status='retido_QA' if r['estado']=='retido' else 'alias_HEAD_sem_contagem_nova' if aliases else 'retido_alias_potencial' if doubts else 'candidato_privado_sem_alias_HEAD'
        rows.append(dict(numero=r['numero_indice'],ano=r['ano_indice'],estado=status,aliases=aliases,aliases_potenciais=doubts,
            fonte_confaz=r['fonte'],notas_publicacao_ratificacao_literais=r.get('notas_publicacao_ratificacao_literais'),
            condicoes_efeitos_literais=r.get('condicoes_efeitos_literais'),limite='Notas e versões de fontes distintas preservadas. Coincidência da identidade não prova igualdade editorial nem autoriza substituição do canônico.'))
    result=dict(commit=head,baseline_v8=dict(path=str(baseline_path.relative_to(ROOT)),sha256=sha(baseline_path.read_bytes()),commit=baseline['head'],cache=baseline['cache'],sha256_cache=baseline['sha256_cache']),
        cabecalhos_canonicos_HEAD=len(headers),delta_normas=len(delta_records),blobs_alias_reexaminados=examined,
        resultados=rows,sem_alias=sum(r['estado']=='candidato_privado_sem_alias_HEAD' for r in rows),aliases=sum(r['estado']=='alias_HEAD_sem_contagem_nova' for r in rows),retidos=sum(r['estado'].startswith('retido') for r in rows),
        criterio='Índice ROOT v8 de blobs HEAD completos, conferido por SHA; diferenças do commit atual atualizadas por OID sem truncar. Possíveis convênios/CONFAZ têm metadados e epígrafe do corpo reexaminados independentemente. Compara tipo Convênio ICMS, número e ano; não usa apenas URL ou slug.',
        limite='Piloto privado. Nenhuma edição, promoção ou inferência de vigência. Dados de ratificação/efeitos permanecem atribuídos ao portal, sem calculá-los.')
    (a.saida/'confronto-head.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['commit','cabecalhos_canonicos_HEAD','delta_normas','blobs_alias_reexaminados','sem_alias','aliases','retidos']}))


if __name__=='__main__':main()

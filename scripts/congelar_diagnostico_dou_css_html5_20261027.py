"""Congela controle suplementar de escopo sem decidir divergências editoriais."""
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(p,obj):
    with p.open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--auditoria',type=Path,action='append',required=True)
    ap.add_argument('--controle',type=Path,action='append',required=True)
    ap.add_argument('--saida',type=Path,required=True)
    a=ap.parse_args();a.saida.mkdir(parents=True,exist_ok=False)
    idx={};files=set();text=[];scope=[];counts=collections.Counter();norms=set();sources=[]
    for p in a.controle:
        files.add(str(p))
        for r in json.loads(p.read_text())['documentos']:idx[r['path']]=(str(p),r)
    for folder in a.auditoria:
        summary=json.loads((folder/'resumo.json').read_text())
        sources.append(dict(auditoria=str(folder),resumo_sha256=sha(folder/'resumo.json')))
        files.update(str(p) for p in folder.iterdir() if p.is_file())
        for m in summary['mapas']:
            assert sha(m['path'])==m['sha256'];files.add(m['path'])
        with gzip.open(folder/'resultados.jsonl.gz','rt') as f:
            for line in f:
                r=json.loads(line);assert r['path'] not in norms;norms.add(r['path'])
                counts['paths']+=1
                if r.get('nativo_excluido'):counts['nativos_excluidos']+=1;continue
                counts['diretos']+=1;counts['documentos_com_tabelas']+=bool(r.get('tabelas_fonte'))
                counts['tabelas']+=r.get('tabelas_fonte',0)
                reasons=[]
                for k in ['erro','md_diverge_mapa','riscos']:
                    if r.get(k):reasons.append(k)
                if not r.get('estrutura_celulas_texto_spans_igual'):reasons.append('matrizes_html5_divergentes')
                if reasons:scope.append(dict(path=r['path'],sha256_md=r.get('sha256_md'),motivos=reasons,detalhe=r))
                if r.get('texto_visivel_igual') is False or r.get('assinatura_numerica_igual') is False:
                    control=idx.get(r['path']);proof=None
                    if control:
                        path,q=control
                        proof=dict(controle=path,sha256_md=q.get('sha256_md'),sha256_fonte=q.get('sha256_fonte'),
                            md_e_fonte_correspondem=q.get('sha256_md')==r['sha256_md'] and q.get('sha256_fonte')==r['sha256_fonte'],
                            igual_fonte=q.get('igual_fonte'),assinatura_numerica_igual=q.get('assinatura_numerica_igual'),
                            headings_comprovados=q.get('headings_comprovados'),primeira_diferenca=q.get('primeira_diferenca'))
                    text.append(dict(path=r['path'],sha256_md=r.get('sha256_md'),sha256_fonte=r.get('sha256_fonte'),
                        diagnostico_bruto=dict(texto_igual=r.get('texto_visivel_igual'),numeros_iguais=r.get('assinatura_numerica_igual')),controle_existente=proof,
                        limite='Diagnóstico bruto suplementar, sem normalização nova. Marcadores/headings/listas devem ser avaliados pelo controle existente; não tratado automaticamente como perda normativa nem como aprovado.'))
    counts['achados_escopo_css_hidden_tachado_tabelas']=len(scope)
    counts['diagnosticos_texto_bruto_fora_escopo']=len(text)
    dump(a.saida/'achados-escopo.json',scope)
    dump(a.saida/'texto-bruto-controles-existentes.json',text)
    dump(a.saida/'resumo-final.json',dict(contagens=counts,fontes=sources,
        criterio='Auditoria privada suplementar somente leitura offline de CSS/hidden/tachados e matrizes HTML5 por tabela/linha/célula/texto/colspan/rowspan, incluindo papel td/th.',
        limite='Não é nova aprovação geral de fidelidade textual. CSS externo/herdado não fornecido não é certificado. Tachado não implica revogação de todo o ato. Nenhuma promoção ou alteração de mapas/canônicos.'))
    files.update(str(p) for p in a.saida.iterdir())
    files.update(['scripts/auditar_dou_css_tabelas_privado_20261027.py','scripts/test_dou_css_tabelas_privado_20261027.py',str(Path(__file__).relative_to(Path.cwd())),
        'scripts/estados/pe_fidelidade_visivel.py','scripts/representacao_html_dou.py',
        'municipais/_indice/_recuperacao_20261027/dou11997-github/final/runtime.json'])
    paths=a.saida/'artefatos.paths.txt';paths.write_text('\n'.join(sorted(files))+'\n');files.add(str(paths))
    records=[dict(arquivo=p,sha256=sha(p),bytes=Path(p).stat().st_size) for p in sorted(files)]
    receipt=a.saida/'manifesto.json';dump(receipt,dict(arquivos=records,bytes=sum(r['bytes'] for r in records),escopo=dict(counts),fontes=sources))
    print(json.dumps(dict(manifesto=str(receipt),sha256=sha(receipt),arquivos=len(records),contagens=counts)))


if __name__=='__main__':main()

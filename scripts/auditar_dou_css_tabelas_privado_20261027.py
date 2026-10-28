"""Auditoria suplementar privada DOU, offline: CSS, ocultos e tabelas HTML5.

Não modifica conversores, registros ou documentos; não infere revogação do ato.
Mantém divergências estruturais e diferenças de papel td/th separadas.
"""
import argparse
import collections
import gzip
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'scripts/bin/qa-20261027/python'),
               str(ROOT/'scripts/bin/qa-html5-20261027/python')]
from auditar_cache_dou import meta_corpo
from estados.pe_fidelidade_visivel import texto_visivel_html, assinatura_numerica
from representacao_html_dou import _CSS_RISCO, _CLASSE_RISCO
from markdown_it import MarkdownIt
import html5lib

assert html5lib.__version__ == '1.1'


def sha(b): return hashlib.sha256(b).hexdigest()


class Riscos(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.flags=[];self.classes=set();self.ids=set();self.tags=set()

    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs);motivos=[];self.tags.add(tag)
        self.classes.update((attrs.get('class') or '').split())
        if attrs.get('id'): self.ids.add(attrs['id'])
        if tag in {'s','strike','del'}:motivos.append('tachado explícito; efeito jurídico não inferido')
        if 'hidden' in attrs or (attrs.get('aria-hidden') or '').lower()=='true':motivos.append('atributo hidden/aria-hidden')
        style=attrs.get('style') or ''
        if _CSS_RISCO.search(style):motivos.append('CSS inline oculto/tachado')
        if '\\' in style or '/*' in style:motivos.append('CSS escapado/comentado exige revisão')
        if _CLASSE_RISCO.search(attrs.get('class') or ''):motivos.append('classe potencialmente histórica exige contexto')
        if re.search(r'(?:height|max-height)\s*:\s*0(?:[a-z%]+)?\b',style,re.I) and re.search(r'overflow\s*:\s*hidden',style,re.I):motivos.append('dimensão zero com overflow oculto')
        if tag=='style':motivos.append('CSS no próprio campo exige contexto')
        if motivos:self.flags.append(dict(tag=tag,linha=self.getpos()[0],coluna=self.getpos()[1],atributos=attrs,motivos=motivos,tag_literal=self.get_starttag_text()))


def riscos(fragmento, pagina):
    p=Riscos();p.feed(fragmento);p.close()
    for block in re.findall(r'<style\b[^>]*>(.*?)</style>',pagina,re.I|re.S):
        for selector,decl in re.findall(r'([^{}]+)\{([^{}]+)\}',block):
            if not _CSS_RISCO.search(decl):continue
            classes=set(re.findall(r'\.([\w-]+)',selector));ids=set(re.findall(r'#([\w-]+)',selector))
            generic=bool(re.search(r'(?:^|,)\s*(?:'+ '|'.join(map(re.escape,sorted(p.tags))) +r')\s*(?:,|$)',selector)) if p.tags else False
            if classes & p.classes or ids & p.ids or 'texto-dou' in selector or generic:
                p.flags.append(dict(motivos=['regra CSS no snapshot potencialmente aplicável; cascade/media não inferidos'],seletor=selector.strip(),declaracao=decl.strip()))
    return p.flags


def matrizes(fragmento):
    parser=html5lib.HTMLParser(tree=html5lib.getTreeBuilder('etree'))
    doc=parser.parse('<!doctype html><html><head><meta charset="utf-8"></head><body>'+fragmento+'</body></html>')
    ns='{http://www.w3.org/1999/xhtml}';tables=[]
    for table in doc.iter(ns+'table'):
        rows=[]
        for row in table.iter(ns+'tr'):
            cells=[]
            for cell in row:
                if cell.tag not in {ns+'td',ns+'th'}:continue
                # Itertext conserva caracteres e entidades; whitespace é a
                # única normalização. Spans e ordem são comparados por linha.
                cells.append(dict(tag=cell.tag.removeprefix(ns),texto=' '.join(''.join(cell.itertext()).split()),colspan=cell.attrib.get('colspan','1'),rowspan=cell.attrib.get('rowspan','1')))
            rows.append(cells)
        tables.append(rows)
    return tables,parser.errors


def sem_papel(tables):
    return [[[{k:v for k,v in cell.items() if k!='tag'} for cell in row] for row in table] for table in tables]


def conferir(path, expected, engine):
    raw=path.read_bytes();meta,body=meta_corpo(raw.decode());result=dict(path=str(path.relative_to(ROOT)),sha256_md=sha(raw),sha256_md_esperado=expected)
    if result['sha256_md']!=expected:result['md_diverge_mapa']=True
    if meta.get('representacao_corpo'):
        return {**result,'nativo_excluido':meta['representacao_corpo']}
    parts=path.relative_to(ROOT).parts
    cache=ROOT/'reguladores/_fonte'/parts[1]/parts[3]/(path.stem+'-'+meta['sha256_html_fonte']+'.html.gz')
    packed=cache.read_bytes();source=gzip.decompress(packed)
    assert sha(source)==meta['sha256_html_fonte'],'SHA da fonte divergente'
    page=source.decode()
    fragment=re.search(r'<div[^>]+class="[^\"]*texto-dou[^\"]*".*?</div>\s*(?=<div|</section|</main)',page,re.S)[0]
    assert len(re.findall(r'<div\b',fragment,re.I))==len(re.findall(r'</div\s*>',fragment,re.I)), 'div incompleta'
    rendered=engine.render(body)
    first=re.search(r'<h1\b[^>]*>.*?</h1>',rendered,re.S)
    assert first and texto_visivel_html(first[0])==' '.join(meta['titulo'].split()),'H1 de metadados inconclusivo'
    rendered=rendered[:first.start()]+rendered[first.end():]
    visible_source=texto_visivel_html(fragment);visible_md=texto_visivel_html(rendered)
    a,errors_a=matrizes(fragment);b,errors_b=matrizes(rendered)
    result.update(fonte_cache=str(cache.relative_to(ROOT)),sha256_cache=sha(packed),sha256_fonte=sha(source),
        riscos=riscos(fragment,page),texto_visivel_igual=visible_source==visible_md,
        assinatura_numerica_igual=assinatura_numerica(visible_source)==assinatura_numerica(visible_md),
        tabelas_fonte=len(a),tabelas_renderizadas=len(b),
        estrutura_celulas_texto_spans_igual=a==b,
        distribuicao_texto_spans_sem_papel_td_th_igual=sem_papel(a)==sem_papel(b),
        sha256_matrizes_fonte=sha(json.dumps(a,ensure_ascii=False,sort_keys=True).encode()),
        sha256_matrizes_renderizadas=sha(json.dumps(b,ensure_ascii=False,sort_keys=True).encode()),
        linhas_fonte=[len(t) for t in a],linhas_renderizadas=[len(t) for t in b],
        erros_html5_fonte=errors_a,erros_html5_renderizado=errors_b)
    if a!=b: result.update(matrizes_fonte=a,matrizes_renderizadas=b)
    assert path.read_bytes()==raw,'MD mudou durante auditoria'
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--mapa',type=Path,action='append',required=True);ap.add_argument('--saida',type=Path,required=True);args=ap.parse_args()
    args.saida.mkdir(parents=True,exist_ok=False)
    inputs=[];paths={}
    for i,p in enumerate(args.mapa,1):
        raw=p.read_bytes();(args.saida/f'mapa-{i}.json').write_bytes(raw);inputs.append(dict(path=str(p),sha256=sha(raw)))
        for name,digest in json.loads(raw).items():
            if name.startswith('reguladores/') and name.endswith('.md') and not any(part.startswith('_') for part in Path(name).parts):
                if name in paths: assert paths[name]==digest,'Mapas conflitantes'
                paths[name]=digest
    engine=MarkdownIt('commonmark',{'html':True}).enable('table').enable('strikethrough')
    counts=collections.Counter();suspects=[]
    with gzip.open(args.saida/'resultados.jsonl.gz','wt',encoding='utf-8') as f:
        for i,(name,digest) in enumerate(paths.items(),1):
            try:r=conferir(ROOT/name,digest,engine)
            except Exception as err:r=dict(path=name,sha256_md_esperado=digest,erro=type(err).__name__+': '+str(err))
            counts['arquivos']+=1
            if r.get('nativo_excluido'):counts['nativos_excluidos']+=1
            else:
                counts['diretos']+=1
                for key in ['erro','md_diverge_mapa','riscos']:
                    if r.get(key):counts[key]+=1
                for key in ['texto_visivel_igual','assinatura_numerica_igual','estrutura_celulas_texto_spans_igual','distribuicao_texto_spans_sem_papel_td_th_igual']:
                    if key in r and not r[key]:counts[key+'_divergente']+=1
                if r.get('erro') or r.get('md_diverge_mapa') or r.get('riscos') or not r.get('estrutura_celulas_texto_spans_igual') or not r.get('texto_visivel_igual'):suspects.append(r)
            f.write(json.dumps(r,ensure_ascii=False)+'\n')
            if i%500==0: print(json.dumps(dict(progresso=i,contagens=counts)),flush=True)
    for p,info in zip(args.mapa,inputs):assert sha(p.read_bytes())==info['sha256'],'Mapa de entrada mudou'
    (args.saida/'suspeitos.json').write_text(json.dumps(suspects,ensure_ascii=False,indent=2)+'\n')
    summary=dict(contagens=counts,mapas=inputs,script_sha256=sha(Path(__file__).read_bytes()),
        runtime=dict(html5lib=html5lib.__version__,markdown_it='4.0.0'),
        criterio='Somente leitura offline. Mesmo DOCTYPE html standards mode/contexto body na fonte e no CommonMark; compara distribuição de linhas/células, texto e colspan/rowspan. Papel td/th permanece comparado, com eventual diferença segregada.',
        limite='Risco CSS/tachado não implica revogação de todo o ato. CSS externo/herdado não fornecido não é certificado. Este diagnóstico não substitui identidade/íntegra nem promove ou modifica documentos.')
    (args.saida/'resumo.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':main()

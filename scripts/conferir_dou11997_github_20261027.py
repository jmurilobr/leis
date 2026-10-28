"""Confere a resposta GitHub já capturada; nenhuma rede ou promoção."""
import argparse
import collections
import difflib
import gzip
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from estados.pe_fidelidade_visivel import texto_visivel_html, assinatura_numerica


class Tabelas(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.eventos = []
        self.dentro = False
        self.celula = None
        self.partes = []
        self.tabelas = self.linhas = self.celulas = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            assert not self.dentro, 'Tabela aninhada exige outra prova'
            self.dentro = True; self.tabelas += 1
            self.eventos.append(('table',))
        elif self.dentro and tag == 'tr':
            self.linhas += 1; self.eventos.append(('tr',))
        elif self.dentro and tag in {'td','th'}:
            assert self.celula is None
            self.celula = tag; self.partes = []; self.celulas += 1
            attrs = dict(attrs)
            self.eventos.append((tag, attrs.get('colspan','1'), attrs.get('rowspan','1')))
        elif self.celula and tag in {'p','div','br','li'}:
            self.partes.append(' ')

    def handle_data(self, data):
        if self.celula:
            self.partes.append(data)

    def handle_endtag(self, tag):
        if tag == self.celula:
            self.eventos.append(('texto', ' '.join(''.join(self.partes).split())))
            self.eventos.append(('/'+tag,)); self.celula = None
        elif self.celula and tag in {'p','div','li'}:
            self.partes.append(' ')
        elif self.dentro and tag in {'table','tr'}:
            self.eventos.append(('/'+tag,))
            if tag == 'table': self.dentro = False


def tabela(texto):
    p = Tabelas(); p.feed(texto); p.close()
    assert not p.dentro and p.celula is None
    return p


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--diretorio', type=Path, required=True)
    ap.add_argument('--saida', type=Path, required=True)
    a = ap.parse_args()
    d = a.diretorio
    pre = json.loads((d/'preflight.json').read_text())
    request = json.loads((d/'request.json').read_text())
    assert sha(request['text'].encode()) == pre['corpo_sha256']
    raw = (d/'response.http').read_bytes()
    assert raw.startswith(b'HTTP/2.0 200 OK\n')
    rendered = re.split(rb'\r?\n\r?\n', raw, maxsplit=1)[1].decode()
    h1s = re.findall(r'<h1\b[^>]*>.*?</h1>', rendered, re.S)
    assert len(h1s) == 1
    title = request['text'].lstrip().split('\n',1)[0].removeprefix('# ')
    assert texto_visivel_html(h1s[0]) == title
    rendered = rendered.replace(h1s[0], '', 1)
    cache = Path('reguladores/_fonte/ministerio-da-economia/2020/portaria-n-11.997-de-12-de-maio-de-2020-256528089-6af8777b39085ed68168257221175ff4f8ef57016a210ceecec6d2a3793c9898.html.gz')
    source = gzip.decompress(cache.read_bytes())
    assert sha(source) == '6af8777b39085ed68168257221175ff4f8ef57016a210ceecec6d2a3793c9898'
    fragment = re.search(r'<div[^>]+class="[^\"]*texto-dou[^\"]*".*?</div>\s*(?=<div|</section|</main)', source.decode(), re.S)[0]
    expected = texto_visivel_html(fragment); actual = texto_visivel_html(rendered)
    tables1 = tabela(fragment); tables2 = tabela(rendered)
    assert expected == actual, 'Texto visível integral difere'
    assert assinatura_numerica(expected) == assinatura_numerica(actual)
    differences = [dict(operacao=op,fonte_intervalo=[i,j],github_intervalo=[k,l],
                        fonte=tables1.eventos[i:j],github=tables2.eventos[k:l])
        for op,i,j,k,l in difflib.SequenceMatcher(a=tables1.eventos,b=tables2.eventos,autojunk=False).get_opcodes()
        if op != 'equal']
    assert len(differences) == 1 and differences[0]['operacao'] == 'insert'
    assert differences[0]['fonte'] == [] and differences[0]['github'] == [('tr',)]
    # Mesmo documento standards mode e contexto body para ambos os fragmentos.
    sys.path.insert(0, str(Path(__file__).resolve().parent/'bin/qa-html5-20261027/python'))
    import html5lib
    assert html5lib.__version__ == '1.1'
    def html5(texto):
        parser = html5lib.HTMLParser(tree=html5lib.getTreeBuilder('etree'))
        doc = parser.parse('<!doctype html><html><head><meta charset="utf-8"></head><body>'+texto+'</body></html>')
        ns = '{http://www.w3.org/1999/xhtml}'
        tables = []
        centered = []
        attributes = collections.Counter()
        for ti, table in enumerate(doc.iter(ns+'table'),1):
            for element in table.iter():
                for key, value in element.attrib.items():
                    attributes[(element.tag.removeprefix(ns),key,value)] += 1
            rows = []
            for ri, tr in enumerate(table.iter(ns+'tr'),1):
                cells = []
                for ci, cell in enumerate(tr,1):
                    if cell.tag not in {ns+'td',ns+'th'}: continue
                    cells.append(dict(tag=cell.tag.removeprefix(ns),texto=' '.join(''.join(cell.itertext()).split()),
                        colspan=cell.attrib.get('colspan','1'),rowspan=cell.attrib.get('rowspan','1')))
                    for child in cell.iter():
                        if 'text-align' in child.attrib.get('style',''):
                            centered.append(dict(tabela=ti,linha=ri,celula=ci,tag=child.tag.removeprefix(ns),
                                style=child.attrib['style'],texto=' '.join(''.join(child.itertext()).split())))
                rows.append(cells)
            tables.append(rows)
        return tables, centered, parser.errors, attributes
    source_rows, source_center, source_errors, source_attrs = html5(fragment)
    github_rows, github_center, github_errors, github_attrs = html5(rendered)
    assert len(source_rows) == len(github_rows) == 4
    assert source_rows == github_rows, 'Distribuição HTML5 de linhas/células ou mesclagens difere'
    assert len(source_center) == 67 and github_center == []
    removed = source_attrs - github_attrs
    added = github_attrs - source_attrs
    assert removed == collections.Counter({('p','style','text-align: center;'):67,
        ('p','class','dou-paragraph'):1949,('table','class','dou-table'):4}), repr(removed)
    assert added == collections.Counter({('table','role','table'):4})
    def atributos(counter):
        return [dict(tag=t,atributo=k,valor=v,quantidade=n) for (t,k,v),n in sorted(counter.items())]
    normalized = dict(criterio='html5lib 1.1, treebuilder etree, mesmo DOCTYPE html standards mode e contexto body. Texto de cada célula conserva sinais e números; normaliza somente whitespace. Colspan/rowspan explícitos e padrão 1.',
        fonte=source_rows,github=github_rows,iguais=True,
        erros_parsing_fonte=source_errors,erros_parsing_github=github_errors,
        alinhamentos_centrais_removidos=source_center,atributos_removidos=atributos(removed),
        atributos_adicionados=atributos(added))
    a.saida.parent.mkdir(parents=True, exist_ok=True)
    with (a.saida.parent/'tabelas-html5.json').open('x') as f:json.dump(normalized,f,ensure_ascii=False,indent=2);f.write('\n')
    result = dict(path=pre['path'],sha256_md=pre['sha256'],endpoint=pre['endpoint'],
        request_sha256=sha((d/'request.json').read_bytes()),response_sha256=sha(raw),
        fonte_cache=str(cache),fonte_sha256=sha(source),h1_removido=title,
        caracteres_visiveis=len(expected),texto_integral_igual=True,assinatura_numerica_igual=True,
        tabelas=tables1.tabelas,aberturas_tr_literais_fonte=tables1.linhas,
        aberturas_tr_literais_github=tables2.linhas,celulas=tables1.celulas,
        estrutura_literal_identica=False,diferencas_eventos_html=differences,
        html5=dict(versao=html5lib.__version__,mesma_distribuicao_linhas_celulas_texto_colspan_rowspan=True,
                   linhas_por_tabela=[len(t) for t in source_rows],
                   celulas_por_tabela=[sum(len(r) for r in t) for t in source_rows]),
        sanitizacao=dict(p_style_text_align_center_removidos=67,p_class_dou_paragraph_removidos_dentro_tabelas=1949,
                         table_class_dou_table_removidos=4,table_role_table_adicionados=4),
        criterio='Uma requisição POST /markdown com corpo completo e mode=gfm. Remove somente o H1 de metadados esperado; compara a sequência integral de texto, pontuação, sinais, números e células com a fonte oficial arquivada. Sem consulta a in.gov.br.',
        limite='GitHub remove CSS de alinhamento central e classes; não há identidade literal de DOM/atributos. HTML5 comprova a mesma distribuição normativa das células e mesclagens após recompor um tr ausente na fonte. Não certifica vigência ou completude do universo jurídico.')
    with a.saida.open('x') as f: json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':main()

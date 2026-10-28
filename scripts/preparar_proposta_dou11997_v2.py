"""Congela proposta individual privada DOU; nunca promove nem consulta rede."""
import argparse
import datetime as dt
import difflib
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import auditar_cache_dou as auditor
import representacao_html_dou as v1
from representacao_html_dou_v2_proposta import representar_fragmento, MODO_HTML_NATIVO_V2, assinatura_dom
from estados.pe_fidelidade_visivel import texto_visivel_html, assinatura_numerica

ROOT = Path(__file__).resolve().parent.parent
REL = 'reguladores/ministerio-da-economia/portarias/2020/portaria-n-11.997-de-12-de-maio-de-2020-256528089.md'
CACHE = 'reguladores/_fonte/ministerio-da-economia/2020/portaria-n-11.997-de-12-de-maio-de-2020-256528089-6af8777b39085ed68168257221175ff4f8ef57016a210ceecec6d2a3793c9898.html.gz'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def dump(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--saida', type=Path, required=True)
    a = ap.parse_args()
    a.saida = a.saida.resolve()
    pre = (ROOT/REL).read_bytes()
    assert sha(pre) == '04322f5512d1d6228ca56d51b1a410864658aee51f56925c97303a92907633f1'
    fonte = gzip.decompress((ROOT/CACHE).read_bytes())
    assert sha(fonte) == '6af8777b39085ed68168257221175ff4f8ef57016a210ceecec6d2a3793c9898'
    fragmento = re.search(r'<div[^>]+class="[^\"]*texto-dou[^\"]*".*?</div>\s*(?=<div|</section|</main)', fonte.decode(), re.S)[0]
    antigo = v1.representar_fragmento(fragmento, modo=v1.MODO_HTML_NATIVO)
    novo = representar_fragmento(fragmento, modo=MODO_HTML_NATIVO_V2)
    meta, _ = auditor.meta_corpo(pre.decode())
    cab = pre.decode().split('\n---\n', 1)[0]
    candidato = cab+'\nrepresentacao_corpo: '+json.dumps(MODO_HTML_NATIVO_V2)+'\n---\n# '+meta['titulo']+'\n\n'+novo
    from markdown_it import MarkdownIt
    engine = MarkdownIt('commonmark', {'html': True}).enable('table').enable('strikethrough')
    fonte_visivel = texto_visivel_html(fragmento)
    render_v1 = engine.render(antigo)
    render_v2 = engine.render(novo)
    assert assinatura_dom(antigo) == assinatura_dom(novo)
    assert fonte_visivel == texto_visivel_html(render_v2)
    assert assinatura_numerica(fonte_visivel) == assinatura_numerica(texto_visivel_html(render_v2))
    # Apenas o namespace privado deste processo recebe o dispatcher proposto.
    with patch.object(auditor, 'representar_fragmento', representar_fragmento):
        registro, _ = auditor.conferir(ROOT/REL, set(), set(), dt.date(2026,10,27),
                                       bruto_md=candidato.encode(), fonte_bytes=fonte)
    a.saida.mkdir(parents=True, exist_ok=False)
    for nome, valor in [('preimagem.md',pre),('candidato.md',candidato.encode()),
                        ('fragmento-oficial.html',fragmento.encode()),('representacao-v1.html',antigo.encode()),
                        ('render-v1.html',render_v1.encode()),('render-v2.html',render_v2.encode())]:
        (a.saida/nome).write_bytes(valor)
    dump(a.saida/'prova.json', dict(path=REL, preimagem_sha256=sha(pre), candidato_sha256=sha(candidato.encode()),
        fonte_cache=CACHE, fonte_sha256=sha(fonte), modo=MODO_HTML_NATIVO_V2,
        transformacao='Somente LF de linhas vazias textuais -> &#10;, após a representação v1. A entidade recompõe o mesmo LF no DOM. Tags e atributos permanecem literais; espaços e sinais não são colapsados.',
        dom_texto_atributos_identicos=True, tabelas=fragmento.count('<table'),
        caracteres_visiveis=dict(fonte=len(fonte_visivel), v1=len(texto_visivel_html(render_v1)), v2=len(texto_visivel_html(render_v2))),
        visible_sha256=sha(fonte_visivel.encode()), assinatura_numerica=assinatura_numerica(fonte_visivel),
        auditor_privado=registro, captura='Metadados originais preservados; não houve recaptura ou consulta de rede.',
        limite='Proposta individual sem promoção. CSS externo/herdado não fornecido no campo não é certificado; nenhum gate de identidade, íntegra ou vigência foi relaxado.'))
    original = (ROOT/'scripts/auditar_cache_dou.py').read_text()
    alterado = original.replace('from representacao_html_dou import representar_fragmento',
                               'from representacao_html_dou_v2_proposta import representar_fragmento')
    assert original != alterado
    (a.saida/'auditor-import-proposto.patch').write_text(''.join(difflib.unified_diff(
        original.splitlines(True), alterado.splitlines(True),
        fromfile='a/scripts/auditar_cache_dou.py', tofile='b/scripts/auditar_cache_dou.py')))
    files = [str(p.relative_to(ROOT)) for p in a.saida.iterdir() if p.is_file()]
    files += [CACHE, 'scripts/representacao_html_dou.py', 'scripts/auditar_cache_dou.py',
              'scripts/representacao_html_dou_v2_proposta.py', 'scripts/test_representacao_html_dou_v2_proposta.py',
              'scripts/preparar_proposta_dou11997_v2.py', 'scripts/qa_municipal_persistente_20261027.py',
              'scripts/estados/pe_fidelidade_visivel.py', 'scripts/dados/dou027-nativo-candidatos-v1-20261027.json',
              '_fonte/operacao_root_20261027/dou027-retido-gfm-diagnostico.json']
    (a.saida/'artefatos.paths.txt').write_text('\n'.join(sorted(set(files)))+'\n')
    files.append(str((a.saida/'artefatos.paths.txt').relative_to(ROOT)))
    records=[dict(arquivo=p,sha256=sha((ROOT/p).read_bytes()),bytes=(ROOT/p).stat().st_size) for p in sorted(set(files))]
    dump(a.saida/'manifesto.json',dict(promocao_automatica=False, arquivos=records, bytes=sum(r['bytes'] for r in records)))
    assert (ROOT/REL).read_bytes() == pre
    print(json.dumps(dict(manifesto=str(a.saida/'manifesto.json'),sha256=sha((a.saida/'manifesto.json').read_bytes()),arquivos=len(records))))


if __name__ == '__main__':
    main()

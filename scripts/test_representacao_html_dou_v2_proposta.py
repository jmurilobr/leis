"""Regressões privadas da representação v2; sem rede ou escritas no acervo."""
import gzip
import hashlib
import re
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import representacao_html_dou as v1
from representacao_html_dou_v2_proposta import (
    MODO_HTML_NATIVO_V2, representar_fragmento, assinatura_dom,
)

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "reguladores/_fonte/ministerio-da-economia/2020/portaria-n-11.997-de-12-de-maio-de-2020-256528089-6af8777b39085ed68168257221175ff4f8ef57016a210ceecec6d2a3793c9898.html.gz"


def fonte_real():
    bruto = gzip.decompress(CACHE.read_bytes())
    assert hashlib.sha256(bruto).hexdigest() == "6af8777b39085ed68168257221175ff4f8ef57016a210ceecec6d2a3793c9898"
    return re.search(r'<div[^>]+class="[^\"]*texto-dou[^\"]*".*?</div>\s*(?=<div|</section|</main)', bruto.decode(), re.S)[0]


def renderizar(texto):
    from markdown_it import MarkdownIt
    return MarkdownIt('commonmark', {'html': True}).enable('table').enable('strikethrough').render(texto)


class RepresentacaoV2(unittest.TestCase):
    def test_caso_real_dom_texto_numeros_e_tabelas(self):
        from estados.pe_fidelidade_visivel import texto_visivel_html, assinatura_numerica
        fonte = fonte_real()
        antigo = representar_fragmento(fonte, modo=v1.MODO_HTML_NATIVO)
        novo = representar_fragmento(fonte, modo=MODO_HTML_NATIVO_V2)
        self.assertEqual(assinatura_dom(antigo), assinatura_dom(novo))
        esperado = texto_visivel_html(fonte)
        self.assertNotEqual(esperado, texto_visivel_html(renderizar(antigo)))
        obtido = texto_visivel_html(renderizar(novo))
        self.assertEqual(esperado, obtido)
        self.assertEqual(assinatura_numerica(esperado), assinatura_numerica(obtido))
        self.assertEqual(fonte.count('<table'), novo.count('<table'))
        self.assertIn('&#10;', novo)

    def test_compatibilidade_v1_byte_a_byte(self):
        exemplos = [fonte_real(), '<div class="texto-dou"><p>A 0,5%; -10,00.  \n\n B</p></div>']
        for fonte in exemplos:
            self.assertEqual(v1.representar_fragmento(fonte, modo=v1.MODO_HTML_NATIVO),
                             representar_fragmento(fonte, modo=v1.MODO_HTML_NATIVO))

    def test_rejeita_elementos_e_css_sensiveis(self):
        for extra in ['<pre>A\n\n B</pre>', '<textarea>A</textarea>', '<xmp>A</xmp>',
                      '<plaintext>A', '<listing>A</listing>'] + [
                      '<p style="white-space: '+css+'">A\n\n B</p>'
                      for css in ['pre', 'pre-wrap', 'pre-line', 'break-spaces', 'inherit', 'preserve']]:
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                representar_fragmento('<div class="texto-dou">'+extra+'</div>', modo=MODO_HTML_NATIVO_V2)

    def test_todos_gates_v1_continuam(self):
        for extra in ['<script>A</script>', '<p hidden>A</p>', '<del>A</del>',
                      '<p style="text-decoration:line-through">A</p>', '<img src="a">',
                      '<p onclick="x()">A</p>', '<p style="display:none">A</p>']:
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                representar_fragmento('<div class="texto-dou">'+extra+'</div>', modo=MODO_HTML_NATIVO_V2)

    def test_atributos_intactos_e_modo_explicito(self):
        fonte = '<div class="texto-dou"><table><tr><td colspan="2" data-k="A &amp; B">0\n\n -1,00</td></tr></table></div>'
        novo = representar_fragmento(fonte, modo=MODO_HTML_NATIVO_V2)
        self.assertEqual(assinatura_dom(fonte), assinatura_dom(novo))
        self.assertIn('colspan="2" data-k="A &amp; B"', novo)
        with self.assertRaises(ValueError):
            representar_fragmento(fonte, modo='desconhecido')


if __name__ == '__main__':
    unittest.main()

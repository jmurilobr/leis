import unittest
from css_contexto_campo import ContextoCSS
class CSSTest(unittest.TestCase):
 def test_tachado_herdado(self):
  q=ContextoCSS([]).conferir('<html><head><style>.old {text-decoration:line-through}</style></head><body class="old"><p>Art. 1º</p></body></html>');self.assertFalse(q['CSS_sem_risco_comprovado'])
 def test_regra_disjunta(self):
  q=ContextoCSS([]).conferir('<html><style>.old{display:none}</style><body><p>Art. 1º</p></body></html>');self.assertTrue(q['CSS_sem_risco_comprovado'])
 def test_campo_classe_ancestral(self):
  q=ContextoCSS([]).conferir('<html><body style="opacity:0"><div class="norma">Art. 1º</div></body></html>',classe_campo='norma');self.assertFalse(q['CSS_sem_risco_comprovado'])
 def test_import_nao_capturado(self):
  q=ContextoCSS([]).conferir('<html><head><style>@import url("a.css");</style></head><body>Art. 1º</body></html>');self.assertFalse(q['CSS_sem_risco_comprovado'])
 def test_pseudo_conteudo(self):
  q=ContextoCSS([]).conferir('<html><style>p:before{content:"1."}</style><body><p>Texto</p></body></html>');self.assertFalse(q['CSS_sem_risco_comprovado'])
 def test_sem_excecao_am_loader(self):
  q=ContextoCSS([]).conferir('<html><style>.m-page{opacity:0}</style><body class="m-page">Texto</body></html>');self.assertFalse(q['CSS_sem_risco_comprovado'])
if __name__=='__main__':unittest.main()

import unittest
from auditar_spl_html_recente import comparar,identidade
class TextoTest(unittest.TestCase):
 def test_literal_valores(self):self.assertTrue(comparar('<p>R$ 0,5 -100 10%</p>','R$ 0,5 -100 10%')['sha256_visivel_fonte'])
 def test_decimal_perdido(self):
  with self.assertRaises(ValueError):comparar('<p>0,5</p>','05')
 def test_sinal_perdido(self):
  with self.assertRaises(ValueError):comparar('<p>-100</p>','100')
 def test_percentual_perdido(self):
  with self.assertRaises(ValueError):comparar('<p>10%</p>','10')
 def test_lista_nao_pode_renumerar(self):
  with self.assertRaises(ValueError):comparar('<p>3. três</p>','3. três')
 def test_epigrafe_fecho_divergentes(self):
  with self.assertRaises(ValueError):identidade('LEI Nº 10.056, DE 07 DE OUTUBRO DE 2026 Art. 1º texto. Aracaju, 08 de outubro de 2026',dict(tipo='Lei Ordinária',numero='10056',data='2026-10-07'))
if __name__=='__main__':unittest.main()

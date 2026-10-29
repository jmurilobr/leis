import unittest
from epigrafe_tokens_html_privado import epigrafe_tokens

def nofallback(*args):raise ValueError('sem epígrafe própria')
class Tokens(unittest.TestCase):
 def test_multiclasse_real(self):
  h="<p class='identifica pdf-CENTER'>PORTARIA Nº 10, DE 4 DE JANEIRO DE 2017</p>"
  self.assertEqual(epigrafe_tokens(h,h,0,nofallback)[0],'PORTARIA Nº 10, DE 4 DE JANEIRO DE 2017')
 def test_ordem_indiferente(self):
  h='<p class="pdf-CENTER identifica">RESOLUÇÃO &amp; A</p>'
  self.assertEqual(epigrafe_tokens(h,h,0,nofallback)[0],'RESOLUÇÃO & A')
 def test_token_exato(self):
  for c in ['nao-identifica','identificadora','identifica-extra']:
   h='<p class="'+c+'">NÃO É EPÍGRAFE</p>'
   with self.assertRaises(ValueError):epigrafe_tokens(h,h,0,nofallback)
 def test_multiplas_retidas(self):
  h='<p class="identifica x">PORTARIA 1</p><p class="x identifica">PORTARIA 2</p>'
  with self.assertRaises(ValueError):epigrafe_tokens(h,h,0,nofallback)
 def test_ausencia_nao_usa_titulo(self):
  h='<h2>PORTARIA 1</h2><p>Art. 1 texto</p>'
  with self.assertRaises(ValueError):epigrafe_tokens(h,h,0,nofallback)
 def test_p_aberto_retido(self):
  h='<p class="identifica">PORTARIA 1'
  with self.assertRaises(ValueError):epigrafe_tokens(h,h,0,nofallback)
 def test_whitespace_HTML(self):
  for c in ['  identifica  pdf-CENTER ','pdf-CENTER\tidentifica','identifica\n\r\fpdf-CENTER']:
   h='<p class="'+c+'">PORTARIA 1</p>'
   self.assertEqual(epigrafe_tokens(h,h,0,nofallback)[0],'PORTARIA 1')
 def test_NBSP_nao_separa_tokens_HTML(self):
  for c in ['identifica\u00a0pdf-CENTER','pdf-CENTER\u00a0identifica']:
   h='<p class="'+c+'">PORTARIA 1</p>'
   with self.assertRaises(ValueError):epigrafe_tokens(h,h,0,nofallback)
if __name__=='__main__':unittest.main()

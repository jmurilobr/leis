from pathlib import Path
import ast,re,unittest
from identidade_cross_snapshot import number
class Identidade(unittest.TestCase):
 def test_sufixo_letra_preservado(self):
  self.assertEqual(number('35.447-A'),'35447-A');self.assertNotEqual(number('35447'),number('35447-A'))
 def test_sufixo_reedicao_numerico(self):
  self.assertEqual(number('2.216-37'),'2216-37');self.assertNotEqual(number('2216-37'),number('2216-36'));self.assertNotEqual(number('2216-37'),number('2216'))
 def test_nao_colapsa_serie_com_barra(self):
  self.assertIsNone(number('42/2017'));self.assertIsNone(number('Decreto 42'))
 def test_tipo_e_data_nao_fundidos(self):
  num=number('8.953');self.assertNotEqual(('dec',num,'2017-01-10'),('dlg',num,'2017-01-10'));self.assertNotEqual(('dec',num,'2017-01-10'),('dec',num,'2017-01-11'))
if __name__=='__main__':unittest.main()

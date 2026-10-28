import unittest
from qualificar_loa8963 import conferir_texto_paginas
class PDFTest(unittest.TestCase):
 def pages(self):
  pages=[f'Orçamento2022\n{n} | LOA2022 - Lei Nº 8.963/2022\n' for n in range(1,523)]
  for n in [1,3,4,5,438]:pages[n-1]='LEI Nº 8.963, DE 13 DE JANEIRO DE 2022\n'
  pages[1]='Expediente institucional';pages[4]+='ANEXO I';pages[437]+='ANEXO II'
  pages[-1]='Quadro de Emenda Modificativa - Projeto de Lei nº 255/2021 (Proposta Orçamentária Anual de 2022)\n522 | LOA2022 - Lei Nº 8.963/2022\n';return pages
 def test_522_paginas(self):self.assertEqual(len(conferir_texto_paginas(self.pages())),522)
 def test_falta_ultima(self):
  with self.assertRaises(ValueError):conferir_texto_paginas(self.pages()[:-1])
 def test_folio_repetido(self):
  p=self.pages();p[12]=p[11]
  with self.assertRaisesRegex(ValueError,'fólio'):conferir_texto_paginas(p)
 def test_outra_identidade(self):
  p=self.pages();p[12]=p[12].replace('8.963','8.819')
  with self.assertRaisesRegex(ValueError,'fólio'):conferir_texto_paginas(p)
 def test_capa_data_divergente(self):
  p=self.pages();p[0]=p[0].replace('13 DE','07 DE')
  with self.assertRaisesRegex(ValueError,'capa'):conferir_texto_paginas(p)
 def test_final_vizinho(self):
  p=self.pages();p[-1]='PORTARIA100 - OUTRO ATO\n522 | LOA2022 - Lei Nº 8.963/2022\n'
  with self.assertRaisesRegex(ValueError,'fechamento'):conferir_texto_paginas(p)
if __name__=='__main__':unittest.main()

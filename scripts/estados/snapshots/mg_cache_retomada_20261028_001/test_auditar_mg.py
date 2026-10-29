import unittest
from auditar_mg import fiel
class Fidelity(unittest.TestCase):
    def test_texto_literal(self):self.assertTrue(fiel('<p>R$ -100,00; 0,5% § 1º.</p>','R$ -100,00; 0,5% § 1º.')['igualdade_literal_nao_branca'])
    def test_sinais_decimais_nao_equivalentes(self):
        for text in ['R$ 100,00; 0,5%','R$ -10000; 0,5%','R$ -100,00; 05%']:
            with self.assertRaises(ValueError):fiel('<p>R$ -100,00; 0,5%</p>',text)
    def test_css_imagem_tachado_rejeitados(self):
        for source in ['<p class="antigo">texto</p>','<p style="display:none">texto</p>','<p><del>texto</del></p>','<p><img src="a"></p>']:
            with self.assertRaises(ValueError):fiel(source,'texto')
    def test_objeto_proprio_requer_outro_contexto(self):
        with self.assertRaises(ValueError):fiel('<p>Fica aprovado o plano.</p>','Fica aprovado o plano.')
    def test_layout_sem_perder_pontuacao(self):self.assertTrue(fiel('<p>Artigo 1º - A.</p><p>Artigo 2º - B;</p>','**Artigo 1º** - A.\n\n**Artigo 2º** - B;')['igualdade_literal_nao_branca'])
if __name__=='__main__':unittest.main()

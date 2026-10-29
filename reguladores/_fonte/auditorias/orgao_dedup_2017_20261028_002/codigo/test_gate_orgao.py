import unittest
from gate_orgao import motivos
class Orgao(unittest.TestCase):
 def test_meta_real(self):
  x='·048H - Aumentar a proporção de acessos da banda larga móvel para 90%/SECRETARIA DO PATRIMÔNIO DA UNIÃO'
  self.assertTrue(motivos(x,x,'Art. 1 texto'))
 def test_aviso_real(self):
  x='...que as edições eletrônicas do Diário Oficial da União produzem os mesmos efeitos legais/Ministério da Saúde/AGÊNCIA NACIONAL DE VIGILÂNCIA SANITÁRIA'
  self.assertTrue(motivos(x,x,'Art. 1 texto'))
 def test_inserir_real(self):
  x='Ministério da Integração Nacional/CONSELHO DELIBERATIVO/INSERIR IMAGENS 1_MIN_23_01 A 04/SECRETARIA NACIONAL'
  self.assertTrue(motivos(x,x,'Art. 1 texto'))
 def test_ausentes_divergentes(self):
  self.assertTrue(motivos('',None,''));self.assertTrue(motivos('Ministério A','Ministério B',''))
 def test_ordinal_militar(self):
  x='Ministério da Defesa/COMANDO DA AERONÁUTICA/II COMANDO AÉREO REGIONAL/9ª COORDENAÇÃO'
  self.assertEqual(motivos(x,x,'Art. 1 texto'),[])
 def test_programa_institucional(self):
  x='Ministério da Defesa/SECRETARIA-GERAL/PROGRAMA CALHA NORTE'
  self.assertEqual(motivos(x,x,'Art. 1 texto'),[])
 def test_mencao_ICP_nao_basta(self):
  x='Presidência da República/INSTITUTO NACIONAL DE TECNOLOGIA DA INFORMAÇÃO'
  self.assertEqual(motivos(x,x,'Regulamenta a ICP-Brasil.'),[])
 def test_aviso_corpo_alerta_sem_remocao(self):
  x='Ministério da Saúde';s='As edições eletrônicas do Diário Oficial da União produzem os mesmos efeitos legais.'
  self.assertTrue(motivos(x,x,s));self.assertEqual(s,'As edições eletrônicas do Diário Oficial da União produzem os mesmos efeitos legais.')
 def test_nivel_vazio(self):
  self.assertTrue(motivos('Ministério A//Secretaria B','Ministério A//Secretaria B',''))
if __name__=='__main__':unittest.main()

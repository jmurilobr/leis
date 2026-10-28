import unittest,json
from aplicar_metadados_edicao import rewrite,read,verify
class Overlay(unittest.TestCase):
 def setUp(self):
  self.blob=b'---\ntitulo: "T"\nnumero: "1"\ndata: "2000-01-01"\nrevogada: null\nversao_texto: "v1"\nedicao: "e1"\n---\n# T\n\nR$ -100,00 0,5%\n';self.values=dict(versao_texto='v2',edicao='e2',observacao_edicao='nota literal')
 def test_corpo_h1_e_dados_protegidos_identicos(self):
  new=rewrite(self.blob,self.values);a,b,_=read(new);self.assertEqual(b,read(self.blob)[1]);self.assertEqual(a['numero'],'1');self.assertIsNone(a['revogada']);self.assertEqual(list(a)[-1],'observacao_edicao')
 def test_mudanca_normativa_rejeitada(self):
  with self.assertRaisesRegex(ValueError,'corpo'):verify(self.blob,rewrite(self.blob,self.values).replace(b'-100,00',b'100,00'),self.values)
 def test_numero_protegido(self):
  with self.assertRaisesRegex(ValueError,'protegido'):verify(self.blob,rewrite(self.blob,self.values).replace(b'numero: "1"',b'numero: "2"'),self.values)
 def test_booleano_status_protegido(self):
  with self.assertRaisesRegex(ValueError,'protegido'):verify(self.blob,rewrite(self.blob,self.values).replace(b'revogada: null',b'revogada: true'),self.values)
 def test_chave_extra_rejeitada(self):
  with self.assertRaisesRegex(ValueError,'escopo'):rewrite(self.blob,dict(self.values,baixado_em='2026-01-01'))
if __name__=='__main__':unittest.main()

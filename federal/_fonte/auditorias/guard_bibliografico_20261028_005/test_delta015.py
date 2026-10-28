from pathlib import Path
import json,gzip,sys,unittest,hashlib
from types import SimpleNamespace
B=Path(__file__).resolve().parent;sys.path.insert(0,str(B));import integridade_anexos_decreto as new,guard80_antecedente as old
P=SimpleNamespace(visual=[],structure=[]);fixtures=json.loads(gzip.decompress((B/'fixtures015.json.gz').read_bytes()))
class CasosReais015(unittest.TestCase):
 def test_real14056_tabela_CLR_nao_e_reproduzida(self):
  r=fixtures['14056'];p=SimpleNamespace(visual=r['visual'],structure=r['structure']);self.assertIsNone(old.anexo_proprio_ausente(r['corpo'],p));result=new.anexo_proprio_ausente(r['corpo'],p);self.assertIsNotNone(result);self.assertEqual(result['classe'],'ponteiro_bibliografico_nao_certifica_integralidade');self.assertIs(result['ausencia_propria_demonstrada'],False)
 def test_real14722_ilegivel_com_asterisco_escapado(self):
  r=fixtures['14722'];p=SimpleNamespace(visual=r['visual'],structure=r['structure']);self.assertIsNone(old.anexo_proprio_ausente(r['corpo'],p));self.assertIsNotNone(new.anexo_proprio_ausente(r['corpo'],p))
 def test_definicao_explicita_asterisco_escapado_permanece_controle(self):
  self.assertIsNone(new.anexo_proprio_ausente(r'Art. 1º Usar a expressão (\*Ilegivel) no campo próprio.',P))
 def test_termo_de_nao_dispensa_lacuna_escapada(self):
  self.assertIsNotNone(new.anexo_proprio_ausente(r'Art. 1º O termo de (\*Ilegivel) será lavrado.',P))
 def test_CLR_referencia_somente_externa_permanece_controle(self):
  text='Art. 1º Observam-se as tabelas anexas à Lei nº 284.\n\n<<ANEXO>>CLR Vol. 02 Ano 1937 Pág. 223 Tabela.';self.assertIsNone(new.anexo_proprio_ausente(text,P))
 def test_CLR_citacao_inline_nao_e_ponteiro_isolado(self):
  text='Art. 1º Registrar a expressão <<ANEXO>>CLR Vol. 02 Ano 1937 Pág. 223 no campo referência do formulário.';self.assertIsNone(new.anexo_proprio_ausente(text,P))
 def test_CLR_atual_com_lista_e_tabela_exige_revisao_sem_certificar_ausencia(self):
  text='Art. 1º A relação acompanha o presente decreto.\n\n1) Maria.\n\n&lt;&lt;ANEXO&gt;&gt;CLR Vol. 02 Ano 1937 Pág. 223 Tabela.';result=new.anexo_proprio_ausente(text,SimpleNamespace(visual=[],structure=[('table',())]));self.assertIsNotNone(result);self.assertIs(result['ausencia_propria_demonstrada'],False)
if __name__=='__main__':unittest.main(verbosity=2)

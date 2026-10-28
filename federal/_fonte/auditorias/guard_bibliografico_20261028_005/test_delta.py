from pathlib import Path
import json,sys,unittest
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parent))
import integridade_anexos_decreto as new,guard74_antecedente as old
P=SimpleNamespace(visual=[],structure=[]);B=Path(__file__).resolve().parent
class PontuacaoDeixis(unittest.TestCase):
 def test_real1908(self):
  text=json.loads((B/'fixture1908.json').read_text())['corpo'];self.assertIsNone(old.anexo_proprio_ausente(text,P));self.assertIsNotNone(new.anexo_proprio_ausente(text,P))
 def test_externa_nao_dispensa_atual_com_virgula(self):
  text='Art. 1º Alteram-se as tabelas anexas à Lei nº 284, com as correções constantes das que acompanham o presente, decreto.\n\n<<ANEXO>>CLBR Vol. 02 Ano 1937 Pág. 223 Tabela.';self.assertIsNotNone(new.anexo_proprio_ausente(text,P))
 def test_mencao_apenas_externa_permanece_controle(self):
  text='Art. 1º Observam-se as tabelas anexas à Lei nº 284.\n\n<<ANEXO>>CLBR Vol. 02 Ano 1937 Pág. 223 Tabela.';self.assertIsNone(new.anexo_proprio_ausente(text,P))
 def test_ponto_e_virgula_atual(self):
  text='Art. 1º Observam-se as tabelas anexas à Lei nº 284 e as que acompanham este; decreto.\n\n<<ANEXO>>CLBR Vol. 02 Ano 1937 Pág. 223 Tabela.';self.assertIsNotNone(new.anexo_proprio_ausente(text,P))
 def test_referencia_atual_sem_ponteiro_nao_inventa_ausencia(self):
  text='Art. 1º A relação acompanha o presente, decreto.\n\n1) Antônio.\n\n2) Maria.';self.assertEqual(old.anexo_proprio_ausente(text,P),new.anexo_proprio_ausente(text,P))
 def test_marcador_em_citacao_sem_ponteiro_isolado(self):
  text='Art. 1º Registrar a expressão <<ANEXO>>CLBR no campo referência do formulário.';self.assertEqual(old.anexo_proprio_ausente(text,P),new.anexo_proprio_ausente(text,P))
if __name__=='__main__':unittest.main(verbosity=2)

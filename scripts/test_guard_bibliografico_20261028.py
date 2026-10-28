"""Regressões de remissões bibliográficas e marcadores literais, sem rede."""
from pathlib import Path
import sys,unittest,json,gzip,hashlib,importlib.util
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import integridade_anexos_decreto as new
assert Path(new.__file__).resolve()==ROOT/'scripts/integridade_anexos_decreto.py'
B=ROOT/'federal/_fonte/auditorias/guard_bibliografico_20261028_005'
def reference(name,expected):
 p=B/(name+'_antecedente.py');assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
 spec=importlib.util.spec_from_file_location(name+'_reference_tests',p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
old74=reference('guard74','3cd60ac4a398a27cc0f646f891e853f6b120b1a963deb4cc9f0ccfd7d6ca0cd0')
old80=reference('guard80','3f581fc23aa987e6b614a9e7bd61e10f69583d07de018685b625cd59758bf466')
P=SimpleNamespace(visual=[],structure=[])
fixtures=json.loads(gzip.decompress((B/'fixtures015.json.gz').read_bytes()))
class PontuacaoDeixis(unittest.TestCase):

    def test_real1908(self):
        text = json.loads((B / 'fixture1908.json').read_text())['corpo']
        self.assertIsNone(old74.anexo_proprio_ausente(text, P))
        self.assertIsNotNone(new.anexo_proprio_ausente(text, P))

    def test_externa_nao_dispensa_atual_com_virgula(self):
        text = 'Art. 1º Alteram-se as tabelas anexas à Lei nº 284, com as correções constantes das que acompanham o presente, decreto.\n\n<<ANEXO>>CLBR Vol. 02 Ano 1937 Pág. 223 Tabela.'
        self.assertIsNotNone(new.anexo_proprio_ausente(text, P))

    def test_mencao_apenas_externa_permanece_controle(self):
        text = 'Art. 1º Observam-se as tabelas anexas à Lei nº 284.\n\n<<ANEXO>>CLBR Vol. 02 Ano 1937 Pág. 223 Tabela.'
        self.assertIsNone(new.anexo_proprio_ausente(text, P))

    def test_ponto_e_virgula_atual(self):
        text = 'Art. 1º Observam-se as tabelas anexas à Lei nº 284 e as que acompanham este; decreto.\n\n<<ANEXO>>CLBR Vol. 02 Ano 1937 Pág. 223 Tabela.'
        self.assertIsNotNone(new.anexo_proprio_ausente(text, P))

    def test_referencia_atual_sem_ponteiro_nao_inventa_ausencia(self):
        text = 'Art. 1º A relação acompanha o presente, decreto.\n\n1) Antônio.\n\n2) Maria.'
        self.assertEqual(old74.anexo_proprio_ausente(text, P), new.anexo_proprio_ausente(text, P))

    def test_marcador_em_citacao_sem_ponteiro_isolado(self):
        text = 'Art. 1º Registrar a expressão <<ANEXO>>CLBR no campo referência do formulário.'
        self.assertEqual(old74.anexo_proprio_ausente(text, P), new.anexo_proprio_ausente(text, P))

class CasosReais015(unittest.TestCase):

    def test_real14056_tabela_CLR_nao_e_reproduzida(self):
        r = fixtures['14056']
        p = SimpleNamespace(visual=r['visual'], structure=r['structure'])
        self.assertIsNone(old80.anexo_proprio_ausente(r['corpo'], p))
        result = new.anexo_proprio_ausente(r['corpo'], p)
        self.assertIsNotNone(result)
        self.assertEqual(result['classe'], 'ponteiro_bibliografico_nao_certifica_integralidade')
        self.assertIs(result['ausencia_propria_demonstrada'], False)

    def test_real14722_ilegivel_com_asterisco_escapado(self):
        r = fixtures['14722']
        p = SimpleNamespace(visual=r['visual'], structure=r['structure'])
        self.assertIsNone(old80.anexo_proprio_ausente(r['corpo'], p))
        self.assertIsNotNone(new.anexo_proprio_ausente(r['corpo'], p))

    def test_definicao_explicita_asterisco_escapado_permanece_controle(self):
        self.assertIsNone(new.anexo_proprio_ausente('Art. 1º Usar a expressão (\\*Ilegivel) no campo próprio.', P))

    def test_termo_de_nao_dispensa_lacuna_escapada(self):
        self.assertIsNotNone(new.anexo_proprio_ausente('Art. 1º O termo de (\\*Ilegivel) será lavrado.', P))

    def test_CLR_referencia_somente_externa_permanece_controle(self):
        text = 'Art. 1º Observam-se as tabelas anexas à Lei nº 284.\n\n<<ANEXO>>CLR Vol. 02 Ano 1937 Pág. 223 Tabela.'
        self.assertIsNone(new.anexo_proprio_ausente(text, P))

    def test_CLR_citacao_inline_nao_e_ponteiro_isolado(self):
        text = 'Art. 1º Registrar a expressão <<ANEXO>>CLR Vol. 02 Ano 1937 Pág. 223 no campo referência do formulário.'
        self.assertIsNone(new.anexo_proprio_ausente(text, P))

    def test_CLR_atual_com_lista_e_tabela_exige_revisao_sem_certificar_ausencia(self):
        text = 'Art. 1º A relação acompanha o presente decreto.\n\n1) Maria.\n\n&lt;&lt;ANEXO&gt;&gt;CLR Vol. 02 Ano 1937 Pág. 223 Tabela.'
        result = new.anexo_proprio_ausente(text, SimpleNamespace(visual=[], structure=[('table', ())]))
        self.assertIsNotNone(result)
        self.assertIs(result['ausencia_propria_demonstrada'], False)

if __name__=='__main__':unittest.main()

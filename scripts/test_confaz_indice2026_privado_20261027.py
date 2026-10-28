"""Regressões offline da seleção privada do índice CONFAZ 2026."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'reguladores/_fonte/auditorias'
CAPTURE = BASE / 'confaz-indice2026-captura-001-20261027/manifesto-captura.json'


class Indice2026(unittest.TestCase):
    def adapted(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            capture = base / 'captura'
            capture.mkdir()
            (capture / 'manifesto-captura.json').write_text(json.dumps(data))
            result = subprocess.run([sys.executable, '-I', str(ROOT / 'scripts/confaz_preparar_qa_indice2026_20261027.py'),
                                     '--captura', str(capture), '--saida', str(base / 'saida')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads((base / 'saida/manifesto-captura.json').read_text())

    def small(self):
        data = json.loads(CAPTURE.read_text())
        data['documentos'] = data['documentos'][:1]
        data['processados'] = 1
        return data

    def test_indice_real_e_retificacao_separada(self):
        result = self.adapted(json.loads(CAPTURE.read_text()))
        self.assertEqual(len(result['paginas']), 126)
        self.assertEqual(len(result['retidos_preflight']), 1)
        self.assertIn('Retificação', result['retidos_preflight'][0]['motivo'])

    def test_fonte_alterada_retida(self):
        data = self.small()
        data['documentos'][0]['fonte']['sha256'] = '0' * 64
        result = self.adapted(data)
        self.assertEqual(result['paginas'], [])
        self.assertIn('Fonte mudou', result['retidos_preflight'][0]['motivo'])

    def test_duas_fontes_principais_retem_ambas(self):
        data = self.small()
        data['documentos'].append(copy.deepcopy(data['documentos'][0]))
        data['processados'] = 2
        result = self.adapted(data)
        self.assertEqual(result['paginas'], [])
        self.assertEqual(len(result['retidos_preflight']), 2)

    def test_confronto_real_exclui_seis_publicados(self):
        data = json.loads((BASE / 'confaz-indice2026-head-002-20261027/confronto-head.json').read_text())
        aliases = [r for r in data['resultados'] if r['estado'] == 'alias_HEAD_sem_contagem_nova']
        self.assertEqual({r['numero'] for r in aliases}, set(range(121, 127)))
        self.assertTrue(all(r['aliases'] and not r['aliases_potenciais'] for r in aliases))
        candidates = json.loads((BASE / 'confaz-indice2026-candidatos-002-20261027/mapa-candidatos.json').read_text())
        self.assertTrue(all(r['numero'] < 121 and not r['alvo_preexistente'] for r in candidates['resultados']))


if __name__ == '__main__':
    unittest.main()

"""Regressões de sinais literais em reparos privados, sem alterar conversores."""
from pathlib import Path
import json
import sys
import unittest
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from preparar_reparos_escapes_ta_20261027 import escapar, comparar, sha


class EscapesTA(unittest.TestCase):
    def test_crases_literais_e_rumos_magneticos(self):
        self.assertEqual(escapar('44º40`14" SW; `caput`.'), '44º40\\`14" SW; \\`caput\\`.')

    def test_hifens_antes_de_texto_e_isolados(self):
        self.assertEqual(escapar('- imposto\n\n-\n\nR$ -2,00\n--\n'), '\\- imposto\n\n\\-\n\nR$ -2,00\n--\n')

    def test_seis_fontes_reais_e_preimagens_intactas(self):
        base = ROOT / 'municipais/_indice/_recuperacao_20261027/reparos-escapes-ta-seis-v2-20261027'
        rows = json.loads((base / 'mapa-candidatos.json').read_text())['candidatos']
        self.assertEqual(len(rows), 6)
        for row in rows:
            raw = (ROOT / row['path']).read_bytes()
            self.assertIn(sha(raw), {row['sha256_preimagem'], row['sha256_candidato']})
            self.assertEqual(sha((ROOT / row['preimagem']).read_bytes()), row['sha256_preimagem'])
            candidate = (ROOT / row['candidato']).read_bytes()
            self.assertEqual(sha(candidate), row['sha256_candidato'])
            body = candidate.decode().split('\n---\n', 1)[1].lstrip('\n').split('\n\n', 1)[1]
            source = (ROOT / row['fonte']['arquivo']).read_bytes()
            self.assertEqual(sha(source), row['fonte']['sha256'])
            self.assertTrue(comparar(source.decode(), body)['aprovado'])


if __name__ == '__main__':
    unittest.main()

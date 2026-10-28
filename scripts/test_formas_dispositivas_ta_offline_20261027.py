"""Formas literais não dispensam identidade, tipo ou integralidade posterior."""
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/bin/qa-20261027/python')]
from recuperar_formas_dispositivas_ta_offline_20261027 import reconhecer


def blocks(*texts):
    return [dict(id=str(i), html='<div>' + text + '</div>') for i, text in enumerate(texts)]


class FormasDispositivas(unittest.TestCase):
    def test_artigo_unico_literal(self):
        result = reconhecer(blocks('Artigo único. Fica revogada a Resolução nº 1.'), 'Resolução', {})
        self.assertEqual(result['forma'], 'artigo_unico_literal')
        self.assertEqual(result['dispositivo'], '0')

    def test_citacao_na_ementa_e_rotulo_vazio_nao_bastam(self):
        for text in ['Altera o artigo único da Lei nº 1.', 'Artigo único da Lei nº 1 é citado.', 'Artigo único.']:
            self.assertIsNone(reconhecer(blocks(text), 'Lei Ordinária', {}))

    def test_portaria_numerada_requer_resolve_anterior(self):
        self.assertIsNone(reconhecer(blocks('1. Nomear o servidor.'), 'Portaria', {}))
        result = reconhecer(blocks('O PRESIDENTE, no uso de suas atribuições, RESOLVE:', '1. Nomear o servidor.'), 'Portaria', {})
        self.assertEqual(result['forma'], 'portaria_resolve_numerada_literal')
        self.assertIsNone(reconhecer(blocks('1. Nomear o servidor.', 'RESOLVE:'), 'Portaria', {}))

    def test_numeracao_nao_amplia_outros_tipos(self):
        self.assertIsNone(reconhecer(blocks('RESOLVE:', '1. Conteúdo.'), 'Ato da Mesa', {}))
        self.assertIsNone(reconhecer(blocks('RESOLVE:', '1. Conteúdo.'), 'Resolução', {}))


if __name__ == '__main__':
    unittest.main()

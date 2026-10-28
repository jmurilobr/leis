"""Índice íntegro, origem de captura e parada imediata sem rede real."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.error
ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / 'scripts/bin/qa-20261027/python'), str(ROOT / 'scripts')]
from preparar_cache_indice_ta_coerente_20261027 import carregar, preparar
import baixar_textos_articulados_indice_coerente_20261027 as coletor
import materializar_textos_articulados_sapl_v5 as v5
import materializar_textos_articulados_sapl_v6 as v6


class ContinuacaoTA(unittest.TestCase):
    host = 'sapl.test.mg.leg.br'

    def fixture(self, base, duplicate=False):
        pages = []
        for n in [1, 2]:
            url = f'https://{self.host}/api/compilacao/textoarticulado/?page_size=100&page={n}'
            raw = json.dumps(dict(results=[dict(id=1 if duplicate else n)], pagination=dict(total_entries=2, next_page=2 if n == 1 else None))).encode()
            path = base / (str(n) + '.json')
            path.write_bytes(raw)
            info = dict(url=url, url_final=url, status=200, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), capturado_em='2026-10-27T17:00:00-03:00')
            meta = path.with_suffix('.meta.json')
            meta.write_text(json.dumps(info))
            pages.append(dict(arquivo=str(path), metadata=str(meta), **info))
        receipt = base / 'manifesto.json'
        receipt.write_text(json.dumps(dict(coerente=True, host=self.host, total=2, ids_unicos=2, vinculo_sigi=dict(codigo_ibge='1234567'), paginas=pages)))
        return receipt

    def test_rejeita_deriva_de_paginacao_com_id_duplicado(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt = self.fixture(Path(tmp), duplicate=True)
            with self.assertRaisesRegex(ValueError, 'ID repetido'):
                carregar(receipt, self.host)

    def test_rejeita_alteracao_da_pagina(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            receipt = self.fixture(base)
            (base / '1.json').write_bytes(b'alterada')
            with self.assertRaises(ValueError):
                carregar(receipt, self.host)

    def test_copia_so_metadados_preserva_captura_e_v5_v6_iguais(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            receipt = self.fixture(base)
            cache = base / 'cache'
            preparar(receipt, self.host, cache)
            info = json.loads(next(cache.glob('*.meta.json')).read_text())
            self.assertEqual(info['capturado_em'], '2026-10-27T17:00:00-03:00')
            self.assertIn('cache_origem', info)
            # O leitor de índice e todas as decisões anteriores ficam iguais.
            with patch.object(v5, 'ROOT', base), patch.object(v6, 'ROOT', base):
                self.assertEqual(v5.carregar_indice(cache), v6.carregar_indice(cache))

    def test_http401_preserva_resposta_e_para_na_primeira_requisicao(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            receipt = self.fixture(base)
            rate = SimpleNamespace(headers={}, limite=SimpleNamespace(esperar=lambda: None))
            error = urllib.error.HTTPError('https://' + self.host, 401, 'Unauthorized', {}, io.BytesIO(b'recusa original'))
            with patch.object(coletor, 'ROOT', base), patch.object(coletor, 'rede_host', return_value=rate) as rede, patch.object(coletor.urllib.request, 'urlopen', side_effect=error) as http:
                with self.assertRaises(coletor.PortalBloqueado):
                    coletor.executar(self.host, base / 'saida', __import__('datetime').date(2026, 10, 27), receipt, [])
                self.assertEqual(http.call_count, 1)
                rede.assert_called_once_with(self.host, 1)
            folder = base / 'municipais/_fonte/texto-articulado-coerente-sapl-20261027' / self.host
            metadata = [p for p in folder.glob('*.meta.json') if json.loads(p.read_text())['status'] == 401]
            self.assertEqual(len(metadata), 1)
            self.assertEqual(metadata[0].with_name(metadata[0].name.replace('.meta.json', '.json')).read_bytes(), b'recusa original')


if __name__ == '__main__':
    unittest.main()
